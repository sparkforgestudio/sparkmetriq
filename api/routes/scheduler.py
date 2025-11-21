# api/routes/scheduler.py
"""
Routes FastAPI pour le Scheduler Multicanal Intelligent.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.scheduler import DraftIn, Draft, PreviewRequest, PreviewOut, ABTestCreate, RecyclePolicy
from api.services.scheduler.ai_copy_service import generate_preview
from api.services.scheduler.planner_service import (
    create_draft, list_drafts, get_draft, delete_draft, generate_weekly_plan,
    get_optimal_posting_times, get_content_calendar
)
from api.services.scheduler.abtest_service import (
    create_ab_test, summarize_ab_test, get_ab_test_recommendations,
    create_ab_test_from_recommendation
)
from api.services.scheduler.recycle_service import (
    schedule_recycle, create_recycle_policy, get_recycle_policies,
    get_recycle_analytics
)
from api.services.scheduler.job_runner import schedule_draft, get_scheduler_status
from api.databases.databases import db

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

# === DRAFTS MANAGEMENT ===

@router.post("/drafts", response_model=dict)
async def create_scheduled_draft(payload: DraftIn, current_user: UserResponse = Depends(get_current_user)):
    """Crée un nouveau draft programmé."""
    draft_id = await create_draft(current_user.id, payload)
    doc = await db["scheduled_drafts"].find_one({"_id": ObjectId(draft_id)})
    
    # Programmer le job
    job_id = await schedule_draft(doc)
    await db["scheduled_drafts"].update_one({"_id": ObjectId(draft_id)}, {"$set":{"job_id": job_id}})
    
    return {"id": draft_id, "job_id": job_id}

@router.get("/drafts", response_model=List[Draft])
async def list_scheduled_drafts(
    muse_id: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Liste les drafts programmés."""
    rows = await list_drafts(current_user.id, muse_id, status, date_from, date_to)
    
    def m(d):
        d["id"] = str(d["_id"])
        del d["_id"]
        return Draft(**d)
    
    return [m(r) for r in rows]

@router.get("/drafts/{draft_id}", response_model=Draft)
async def get_scheduled_draft(draft_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Récupère un draft par ID."""
    doc = await get_draft(current_user.id, draft_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return Draft(**doc)

@router.put("/drafts/{draft_id}", response_model=dict)
async def update_scheduled_draft(
    draft_id: str, 
    updates: dict, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Met à jour un draft."""
    from api.services.scheduler.planner_service import update_draft
    
    success = await update_draft(current_user.id, draft_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return {"ok": True}

@router.delete("/drafts/{draft_id}", response_model=dict)
async def remove_draft(draft_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Supprime un draft."""
    ok = await delete_draft(current_user.id, draft_id)
    return {"ok": ok}

# === AI PREVIEW ===

@router.post("/preview", response_model=PreviewOut)
async def preview_caption(payload: PreviewRequest, current_user: UserResponse = Depends(get_current_user)):
    """Génère un aperçu de contenu via IA."""
    res = await generate_preview(
        payload.platform, 
        payload.muse_id, 
        payload.tone or "flirty", 
        payload.objective or "teasing", 
        payload.language or "en", 
        payload.prompt
    )
    return PreviewOut(**res)

# === WEEKLY PLANNING ===

@router.post("/weekly_plan", response_model=dict)
async def create_weekly_plan(
    muse_id: str, 
    start_day: datetime, 
    tone: str = "flirty", 
    objective: str = "teasing", 
    current_user: UserResponse = Depends(get_current_user)
):
    """Crée un plan hebdomadaire automatique."""
    ids = await generate_weekly_plan(current_user.id, muse_id, start_day, tone, objective)
    
    # Auto-programmer les jobs
    for did in ids:
        doc = await db["scheduled_drafts"].find_one({"_id": ObjectId(did)})
        job_id = await schedule_draft(doc)
        await db["scheduled_drafts"].update_one({"_id": ObjectId(did)}, {"$set":{"job_id": job_id}})
    
    return {"created": ids}

@router.get("/optimal_times/{platform}", response_model=dict)
async def get_optimal_times(
    platform: str, 
    muse_id: str, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère les heures optimales de publication."""
    times = await get_optimal_posting_times(platform, muse_id)
    return {"platform": platform, "optimal_times": times}

@router.get("/calendar", response_model=dict)
async def get_calendar(
    muse_id: str,
    start_date: datetime,
    end_date: datetime,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère le calendrier de contenu."""
    calendar = await get_content_calendar(current_user.id, muse_id, start_date, end_date)
    return calendar

# === A/B TESTING ===

@router.post("/abtest", response_model=dict)
async def create_abtest(payload: ABTestCreate, current_user: UserResponse = Depends(get_current_user)):
    """Crée un test A/B."""
    r = await create_ab_test(current_user.id, payload)
    return r

@router.get("/abtest/{campaign_id}/summary", response_model=dict)
async def abtest_summary(campaign_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Résume les résultats d'un test A/B."""
    return await summarize_ab_test(current_user.id, campaign_id)

@router.get("/abtest/recommendations", response_model=dict)
async def get_abtest_recommendations(
    muse_id: str,
    platform: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère des recommandations pour les tests A/B."""
    recommendations = await get_ab_test_recommendations(current_user.id, muse_id, platform)
    return {"recommendations": recommendations}

@router.post("/abtest/auto", response_model=dict)
async def create_auto_abtest(
    muse_id: str,
    platform: str,
    recommendation_type: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Crée un test A/B automatique basé sur une recommandation."""
    result = await create_ab_test_from_recommendation(current_user.id, muse_id, platform, recommendation_type)
    return result

# === RECYCLING ===

@router.post("/recycle", response_model=dict)
async def run_recycle(
    muse_id: str, 
    policy: RecyclePolicy, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Lance le recyclage de contenu."""
    ids = await schedule_recycle(current_user.id, muse_id, policy.model_dump())
    
    # Auto-programmer les jobs
    for did in ids:
        doc = await db["scheduled_drafts"].find_one({"_id": ObjectId(did)})
        job_id = await schedule_draft(doc)
        await db["scheduled_drafts"].update_one({"_id": ObjectId(did)}, {"$set":{"job_id": job_id}})
    
    return {"created": ids}

@router.post("/recycle/policy", response_model=dict)
async def create_recycle_policy_endpoint(
    muse_id: str,
    policy: RecyclePolicy,
    current_user: UserResponse = Depends(get_current_user)
):
    """Crée une politique de recyclage."""
    policy_id = await create_recycle_policy(current_user.id, muse_id, policy.model_dump())
    return {"policy_id": policy_id}

@router.get("/recycle/policies", response_model=dict)
async def get_recycle_policies_endpoint(
    muse_id: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère les politiques de recyclage."""
    policies = await get_recycle_policies(current_user.id, muse_id)
    return {"policies": policies}

@router.get("/recycle/analytics", response_model=dict)
async def get_recycle_analytics_endpoint(
    muse_id: str,
    days: int = 30,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère les analytics de recyclage."""
    analytics = await get_recycle_analytics(current_user.id, muse_id, days)
    return analytics

# === SCHEDULER STATUS ===

@router.get("/status", response_model=dict)
async def get_scheduler_status_endpoint(current_user: UserResponse = Depends(get_current_user)):
    """Récupère le statut du scheduler."""
    return await get_scheduler_status()

# === PUBLISH HISTORY ===

@router.get("/history", response_model=dict)
async def get_publish_history(
    muse_id: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère l'historique des publications."""
    from api.services.scheduler.publish_service import get_publish_history
    
    history = await get_publish_history(current_user.id, muse_id, platform, limit)
    return {"history": history}