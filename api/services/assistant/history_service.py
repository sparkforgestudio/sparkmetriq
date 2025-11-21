# api/services/assistant/history_service.py
"""
Service d'historique des recommandations et feedback.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from api.databases.databases import db

async def log_recommendation(tenant_id: str, muse_id: str, plan_month: Optional[str], text: str) -> str:
    """Enregistre une recommandation dans l'historique."""
    doc = {
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "plan_month": plan_month,
        "recommendation": text,
        "applied": False,
        "feedback": None,
        "kpi_after": None,
        "ts": datetime.now(timezone.utc)
    }
    r = await db["ai_reco_history"].insert_one(doc)
    return str(r.inserted_id)

async def set_feedback(tenant_id: str, reco_id: str, applied: bool, feedback: Optional[str], kpi_after: Optional[Dict[str, float]]):
    """Met à jour le feedback d'une recommandation."""
    await db["ai_reco_history"].update_one(
        {"_id": ObjectId(reco_id), "tenant_id": tenant_id},
        {
            "$set": {
                "applied": applied,
                "feedback": feedback,
                "kpi_after": kpi_after,
                "feedback_at": datetime.now(timezone.utc)
            }
        }
    )

async def get_recommendation_history(tenant_id: str, muse_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Récupère l'historique des recommandations."""
    cursor = db["ai_reco_history"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id
    }).sort("ts", -1).limit(limit)
    
    recommendations = []
    for rec in await cursor.to_list(None):
        rec["id"] = str(rec["_id"])
        del rec["_id"]
        recommendations.append(rec)
    
    return recommendations

async def get_recommendation_stats(tenant_id: str, muse_id: str, days: int = 30) -> Dict[str, Any]:
    """Calcule les statistiques des recommandations."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Statistiques générales
    total_recos = await db["ai_reco_history"].count_documents({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "ts": {"$gte": cutoff}
    })
    
    applied_recos = await db["ai_reco_history"].count_documents({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "ts": {"$gte": cutoff},
        "applied": True
    })
    
    # Statistiques de feedback
    feedback_stats = await db["ai_reco_history"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "ts": {"$gte": cutoff},
                "feedback": {"$ne": None}
            }
        },
        {
            "$group": {
                "_id": "$feedback",
                "count": {"$sum": 1}
            }
        }
    ]).to_list(None)
    
    feedback_summary = {item["_id"]: item["count"] for item in feedback_stats}
    
    # Taux d'application
    application_rate = (applied_recos / total_recos) if total_recos > 0 else 0.0
    
    # Recommandations les plus appliquées
    top_applied = await db["ai_reco_history"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "ts": {"$gte": cutoff},
                "applied": True
            }
        },
        {
            "$group": {
                "_id": "$recommendation",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        },
        {
            "$limit": 5
        }
    ]).to_list(None)
    
    return {
        "total_recommendations": total_recos,
        "applied_recommendations": applied_recos,
        "application_rate": application_rate,
        "feedback_summary": feedback_summary,
        "top_applied_recommendations": top_applied,
        "period_days": days
    }

async def track_recommendation_outcome(tenant_id: str, reco_id: str, outcome: Dict[str, Any]) -> bool:
    """Suit le résultat d'une recommandation appliquée."""
    try:
        await db["ai_reco_history"].update_one(
            {
                "_id": ObjectId(reco_id),
                "tenant_id": tenant_id
            },
            {
                "$set": {
                    "outcome": outcome,
                    "outcome_tracked_at": datetime.now(timezone.utc)
                }
            }
        )
        return True
    except Exception as e:
        print(f"Erreur lors du suivi du résultat: {e}")
        return False

async def get_recommendation_effectiveness(tenant_id: str, muse_id: str) -> Dict[str, Any]:
    """Analyse l'efficacité des recommandations."""
    # Analyser les KPIs avant/après application des recommandations
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    
    # Récupérer les recommandations avec KPIs
    recos_with_kpis = await db["ai_reco_history"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "ts": {"$gte": cutoff},
        "applied": True,
        "kpi_after": {"$ne": None}
    }).to_list(None)
    
    if not recos_with_kpis:
        return {
            "effectiveness_score": 0.0,
            "improvement_areas": [],
            "successful_patterns": [],
            "sample_size": 0
        }
    
    # Analyser les améliorations
    improvements = []
    for reco in recos_with_kpis:
        kpi_after = reco.get("kpi_after", {})
        if kpi_after:
            improvements.append(kpi_after)
    
    # Calculer un score d'efficacité global
    effectiveness_score = 0.0
    if improvements:
        # Score basé sur les améliorations moyennes
        avg_improvement = sum(imp.get("improvement_percent", 0) for imp in improvements) / len(improvements)
        effectiveness_score = min(avg_improvement / 100, 1.0)  # Normaliser entre 0 et 1
    
    # Identifier les patterns de succès
    successful_patterns = []
    for reco in recos_with_kpis:
        if reco.get("feedback") == "useful":
            successful_patterns.append({
                "recommendation": reco["recommendation"][:100],  # Tronquer
                "kpi_improvement": reco.get("kpi_after", {}).get("improvement_percent", 0)
            })
    
    return {
        "effectiveness_score": effectiveness_score,
        "improvement_areas": list(set(imp.get("area", "general") for imp in improvements)),
        "successful_patterns": successful_patterns[:5],  # Top 5
        "sample_size": len(recos_with_kpis)
    }

async def export_recommendation_data(tenant_id: str, muse_id: str, format: str = "json") -> Dict[str, Any]:
    """Exporte les données de recommandations."""
    cursor = db["ai_reco_history"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id
    }).sort("ts", -1)
    
    data = []
    for reco in await cursor.to_list(None):
        reco["id"] = str(reco["_id"])
        del reco["_id"]
        data.append(reco)
    
    return {
        "format": format,
        "data": data,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(data)
    }

async def cleanup_old_recommendations(tenant_id: str, days_to_keep: int = 365) -> int:
    """Nettoie les anciennes recommandations."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    
    result = await db["ai_reco_history"].delete_many({
        "tenant_id": tenant_id,
        "ts": {"$lt": cutoff}
    })
    
    return result.deleted_count
