# api/routes/assistant.py
"""
Routes FastAPI pour l'Assistant IA Stratégique.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.assistant import ActionPlanIn, ActionPlan, Alert, CollabSuggestion, TrendInsight, RecoRecord
from api.services.assistant.plan_service import build_monthly_plan, get_plan_history
from api.services.assistant.alerts_service import compute_basic_alerts, persist_alerts, acknowledge_alert, close_alert, get_alert_summary
from api.services.assistant.collab_service import suggest_collabs, get_collab_history, generate_collab_content_ideas
from api.services.assistant.trends_service import search_trends, get_trend_insights
from api.services.assistant.history_service import log_recommendation, set_feedback, get_recommendation_history, get_recommendation_stats
from api.databases.databases import db

router = APIRouter(prefix="/assistant", tags=["assistant"])

# === PLANS D'ACTION MENSUELS ===

@router.post("/plan", response_model=ActionPlan)
async def generate_monthly_plan(payload: ActionPlanIn, current_user: UserResponse = Depends(get_current_user)):
    """Génère un plan d'action mensuel personnalisé."""
    tenant_id = current_user.id
    res = await build_monthly_plan(tenant_id, payload)
    
    now = utcnow()
    doc = {
        "tenant_id": tenant_id,
        "muse_id": payload.muse_id,
        "month": payload.month,
        "goals": res.get("goals", []),
        "actions": res.get("actions", []),
        "insights": res.get("insights", []),
        "created_at": now,
        "version": 1
    }
    
    r = await db["ai_action_plans"].update_one(
        {"tenant_id": tenant_id, "muse_id": payload.muse_id, "month": payload.month},
        {"$set": doc}, upsert=True
    )
    
    saved = await db["ai_action_plans"].find_one({
        "tenant_id": tenant_id,
        "muse_id": payload.muse_id,
        "month": payload.month
    })
    
    saved["id"] = str(saved["_id"])
    del saved["_id"]
    return ActionPlan(**saved)

@router.get("/plan/{muse_id}/{month}", response_model=ActionPlan)
async def get_monthly_plan(muse_id: str, month: str, current_user: UserResponse = Depends(get_current_user)):
    """Récupère un plan d'action mensuel existant."""
    plan = await db["ai_action_plans"].find_one({
        "tenant_id": current_user.id,
        "muse_id": muse_id,
        "month": month
    })
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan["id"] = str(plan["_id"])
    del plan["_id"]
    return ActionPlan(**plan)

@router.get("/plan/history/{muse_id}", response_model=List[ActionPlan])
async def get_plan_history_endpoint(muse_id: str, limit: int = 10, current_user: UserResponse = Depends(get_current_user)):
    """Récupère l'historique des plans d'un créateur."""
    plans = await get_plan_history(current_user.id, muse_id, limit)
    return plans

# === ALERTES STRATÉGIQUES ===

@router.post("/alerts/run", response_model=dict)
async def run_alerts(muse_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Lance le calcul des alertes pour un créateur."""
    tenant_id = current_user.id
    alerts = await compute_basic_alerts(tenant_id, muse_id)
    await persist_alerts(tenant_id, muse_id, alerts)
    return {"created": len(alerts)}

@router.get("/alerts/{muse_id}", response_model=List[Alert])
async def list_alerts(
    muse_id: str, 
    status: Optional[str] = None, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Liste les alertes d'un créateur."""
    q = {"tenant_id": current_user.id, "muse_id": muse_id}
    if status: 
        q["status"] = status
    
    cur = db["ai_alerts"].find(q).sort("ts", -1)
    res = []
    for d in await cur.to_list(None):
        d["id"] = str(d["_id"])
        del d["_id"]
        res.append(Alert(**d))
    return res

@router.post("/alerts/{alert_id}/acknowledge", response_model=dict)
async def acknowledge_alert_endpoint(alert_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Marque une alerte comme acquittée."""
    success = await acknowledge_alert(current_user.id, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"ok": True}

@router.post("/alerts/{alert_id}/close", response_model=dict)
async def close_alert_endpoint(alert_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Ferme une alerte."""
    success = await close_alert(current_user.id, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"ok": True}

@router.get("/alerts/{muse_id}/summary", response_model=dict)
async def get_alert_summary_endpoint(muse_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Récupère un résumé des alertes."""
    summary = await get_alert_summary(current_user.id, muse_id)
    return summary

# === SUGGESTIONS DE COLLABORATIONS ===

@router.get("/collabs/{muse_id}", response_model=CollabSuggestion)
async def get_collab_suggestions(muse_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Récupère des suggestions de collaboration."""
    tenant_id = current_user.id
    muse = await db["muses"].find_one({"tenant_id": tenant_id, "muse_id": muse_id}) or {}
    niches = muse.get("niches", []) or ["cosplay"]
    
    out = await suggest_collabs(tenant_id, muse_id, niches, top_k=5)
    doc = {
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "profiles": out["profiles"],
        "outreach_template": out["outreach_template"],
        "ts": utcnow()
    }
    
    r = await db["ai_collab_suggestions"].insert_one(doc)
    d = {**doc, "id": str(r.inserted_id)}
    return d

@router.get("/collabs/history/{muse_id}", response_model=List[CollabSuggestion])
async def get_collab_history_endpoint(muse_id: str, limit: int = 10, current_user: UserResponse = Depends(get_current_user)):
    """Récupère l'historique des suggestions de collaboration."""
    collabs = await get_collab_history(current_user.id, muse_id, limit)
    return collabs

@router.get("/collabs/ideas/{muse_id}", response_model=dict)
async def get_collab_content_ideas_endpoint(
    muse_id: str, 
    niche: str = "cosplay",
    current_user: UserResponse = Depends(get_current_user)
):
    """Génère des idées de contenu collaboratif."""
    ideas = await generate_collab_content_ideas(current_user.id, muse_id, niche)
    return {"ideas": ideas}

# === DÉTECTION DE TENDANCES ===

@router.get("/trends/{muse_id}", response_model=List[TrendInsight])
async def get_trends(muse_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Récupère les tendances pertinentes pour un créateur."""
    tenant_id = current_user.id
    muse = await db["muses"].find_one({"tenant_id": tenant_id, "muse_id": muse_id}) or {}
    niches = muse.get("niches", []) or ["cosplay"]
    
    items = await search_trends(tenant_id, niches, limit=5)
    return items

@router.get("/trends/{muse_id}/insights", response_model=dict)
async def get_trend_insights_endpoint(muse_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Récupère des insights sur les tendances."""
    tenant_id = current_user.id
    muse = await db["muses"].find_one({"tenant_id": tenant_id, "muse_id": muse_id}) or {}
    niches = muse.get("niches", []) or ["cosplay"]
    
    insights = await get_trend_insights(tenant_id, muse_id, niches)
    return insights

# === HISTORIQUE DES RECOMMANDATIONS ===

@router.post("/history", response_model=dict)
async def add_recommendation(
    muse_id: str, 
    text: str, 
    plan_month: Optional[str] = None, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Ajoute une recommandation à l'historique."""
    rid = await log_recommendation(current_user.id, muse_id, plan_month, text)
    return {"id": rid}

@router.post("/history/{reco_id}/feedback", response_model=dict)
async def set_reco_feedback(
    reco_id: str, 
    applied: bool, 
    feedback: Optional[str] = None, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Met à jour le feedback d'une recommandation."""
    await set_feedback(current_user.id, reco_id, applied, feedback, None)
    return {"ok": True}

@router.get("/history/{muse_id}", response_model=List[RecoRecord])
async def get_recommendation_history_endpoint(
    muse_id: str, 
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère l'historique des recommandations."""
    history = await get_recommendation_history(current_user.id, muse_id, limit)
    return history

@router.get("/history/{muse_id}/stats", response_model=dict)
async def get_recommendation_stats_endpoint(
    muse_id: str, 
    days: int = 30,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère les statistiques des recommandations."""
    stats = await get_recommendation_stats(current_user.id, muse_id, days)
    return stats

# === DASHBOARD ASSISTANT ===

@router.get("/dashboard/{muse_id}", response_model=dict)
async def get_assistant_dashboard(muse_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Récupère le tableau de bord de l'assistant."""
    tenant_id = current_user.id
    
    # Récupérer les données récentes
    recent_plan = await db["ai_action_plans"].find_one({
        "tenant_id": tenant_id,
        "muse_id": muse_id
    }, sort=[("created_at", -1)])
    
    recent_alerts = await db["ai_alerts"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "status": "open"
    }).sort("ts", -1).limit(5).to_list(None)
    
    recent_collabs = await db["ai_collab_suggestions"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id
    }).sort("ts", -1).limit(3).to_list(None)
    
    recent_trends = await search_trends(tenant_id, ["cosplay"], limit=3)
    
    # Statistiques des recommandations
    reco_stats = await get_recommendation_stats(tenant_id, muse_id, 30)
    
    return {
        "recent_plan": recent_plan,
        "recent_alerts": recent_alerts,
        "recent_collabs": recent_collabs,
        "recent_trends": recent_trends,
        "recommendation_stats": reco_stats,
        "last_updated": utcnow().isoformat()
    }



