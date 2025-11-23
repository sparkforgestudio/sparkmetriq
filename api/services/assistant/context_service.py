# api/services/assistant/context_service.py
"""
Service d'agrégation de contexte pour l'Assistant IA Stratégique.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from api.databases.databases import db

async def load_creator_context(tenant_id: str, muse_id: str, date_from: datetime, date_to: datetime) -> Dict[str, Any]:
    """Charge le contexte complet d'un créateur pour l'IA."""
    # KPIs basiques
    msgs = await db["chat_messages"].count_documents({
        "tenant_id": tenant_id, 
        "muse_id": muse_id, 
        "timestamp": {"$gte": date_from, "$lt": date_to}
    })
    
    payers = await db["payments"].distinct("user_hash", {
        "tenant_id": tenant_id, 
        "muse_id": muse_id, 
        "status": "confirmed", 
        "ts": {"$gte": date_from, "$lt": date_to}
    })
    
    gmv_result = await db["payments"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id, 
                "muse_id": muse_id, 
                "status": "confirmed", 
                "ts": {"$gte": date_from, "$lt": date_to}
            }
        },
        {
            "$group": {
                "_id": None, 
                "gmv": {"$sum": "$amount"}
            }
        },
        {
            "$project": {
                "_id": 0, 
                "gmv": 1
            }
        }
    ]).to_list(1)
    
    gmv_val = float(gmv_result[0]["gmv"]) if gmv_result else 0.0

    # PPV analytics
    ppv_result = await db["ppv_logs"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id, 
                "muse_id": muse_id, 
                "ts": {"$gte": date_from, "$lt": date_to}
            }
        },
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "avg_price": {"$avg": "$price"}
            }
        }
    ]).to_list(None)
    
    ppv_stats = {item["_id"]: item for item in ppv_result}
    ppv_sent = ppv_stats.get("sent", {}).get("count", 0)
    ppv_paid = ppv_stats.get("paid", {}).get("count", 0)
    ppv_conversion = (ppv_paid / ppv_sent) if ppv_sent > 0 else 0.0

    # Publications par plateforme
    platform_stats = await db["publish_logs"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id, 
                "muse_id": muse_id, 
                "ts": {"$gte": date_from, "$lt": date_to},
                "status": "published"
            }
        },
        {
            "$group": {
                "_id": "$platform",
                "count": {"$sum": 1}
            }
        }
    ]).to_list(None)
    
    platforms = {item["_id"]: item["count"] for item in platform_stats}

    # persona, niches: à lire d'une collection `muses` si elle existe
    muse = await db["muses"].find_one({"tenant_id": tenant_id, "muse_id": muse_id}) or {}
    persona = muse.get("persona", {})
    niches = muse.get("niches", [])
    bio = muse.get("bio", "")
    tone = muse.get("tone", "flirty")

    # Calculer les tendances de croissance
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    
    # Messages cette semaine vs semaine précédente
    msgs_this_week = await db["chat_messages"].count_documents({
        "tenant_id": tenant_id, 
        "muse_id": muse_id, 
        "timestamp": {"$gte": week_ago, "$lt": now}
    })
    
    msgs_last_week = await db["chat_messages"].count_documents({
        "tenant_id": tenant_id, 
        "muse_id": muse_id, 
        "timestamp": {"$gte": two_weeks_ago, "$lt": week_ago}
    })
    
    message_growth = ((msgs_this_week - msgs_last_week) / msgs_last_week * 100) if msgs_last_week > 0 else 0.0

    # Revenus cette semaine vs semaine précédente
    gmv_this_week = await db["payments"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id, 
                "muse_id": muse_id, 
                "status": "confirmed", 
                "ts": {"$gte": week_ago, "$lt": now}
            }
        },
        {
            "$group": {
                "_id": None, 
                "gmv": {"$sum": "$amount"}
            }
        }
    ]).to_list(1)
    
    gmv_last_week = await db["payments"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id, 
                "muse_id": muse_id, 
                "status": "confirmed", 
                "ts": {"$gte": two_weeks_ago, "$lt": week_ago}
            }
        },
        {
            "$group": {
                "_id": None, 
                "gmv": {"$sum": "$amount"}
            }
        }
    ]).to_list(1)
    
    gmv_this_week_val = float(gmv_this_week[0]["gmv"]) if gmv_this_week else 0.0
    gmv_last_week_val = float(gmv_last_week[0]["gmv"]) if gmv_last_week else 0.0
    revenue_growth = ((gmv_this_week_val - gmv_last_week_val) / gmv_last_week_val * 100) if gmv_last_week_val > 0 else 0.0

    return {
        "kpIs": {
            "messages": msgs, 
            "payers": len(payers), 
            "gmv": gmv_val,
            "ppv_sent": ppv_sent,
            "ppv_paid": ppv_paid,
            "ppv_conversion": ppv_conversion,
            "platforms": platforms,
            "message_growth": message_growth,
            "revenue_growth": revenue_growth
        },
        "persona": {
            "tone": tone,
            "bio": bio,
            **persona
        },
        "niches": niches,
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat()
        }
    }

async def get_creator_performance_summary(tenant_id: str, muse_id: str, days: int = 30) -> Dict[str, Any]:
    """Résumé des performances d'un créateur."""
    now = datetime.now(timezone.utc)
    date_from = now - timedelta(days=days)
    
    context = await load_creator_context(tenant_id, muse_id, date_from, now)
    
    # Calculer des métriques dérivées
    kpis = context["kpIs"]
    arpu = kpis["gmv"] / kpis["payers"] if kpis["payers"] > 0 else 0.0
    
    # Identifier les plateformes les plus performantes
    top_platform = max(kpis["platforms"].items(), key=lambda x: x[1]) if kpis["platforms"] else ("none", 0)
    
    # Score de performance global (0-100)
    performance_score = 0
    if kpis["message_growth"] > 0:
        performance_score += 20
    if kpis["revenue_growth"] > 0:
        performance_score += 30
    if kpis["ppv_conversion"] > 0.1:  # 10% de conversion PPV
        performance_score += 25
    if kpis["payers"] > 10:  # Plus de 10 payeurs
        performance_score += 25
    
    return {
        "performance_score": min(performance_score, 100),
        "arpu": arpu,
        "top_platform": top_platform[0],
        "growth_trend": "positive" if kpis["revenue_growth"] > 0 else "negative" if kpis["revenue_growth"] < -10 else "stable",
        "engagement_level": "high" if kpis["message_growth"] > 20 else "medium" if kpis["message_growth"] > 0 else "low",
        "ppv_performance": "excellent" if kpis["ppv_conversion"] > 0.15 else "good" if kpis["ppv_conversion"] > 0.08 else "needs_improvement"
    }

async def get_creator_benchmarks(tenant_id: str, muse_id: str, niche: str) -> Dict[str, Any]:
    """Récupère les benchmarks pour un créateur dans sa niche."""
    # Pour V1, on utilise des benchmarks simulés
    # Dans une version future, cela pourrait venir d'une analyse des autres créateurs de la même niche
    
    benchmarks = {
        "cosplay": {
            "avg_engagement_rate": 0.08,
            "avg_ppv_conversion": 0.12,
            "avg_arpu": 25.0,
            "top_platforms": ["instagram", "reddit", "tiktok"],
            "avg_posts_per_week": 5
        },
        "fitness": {
            "avg_engagement_rate": 0.06,
            "avg_ppv_conversion": 0.10,
            "avg_arpu": 30.0,
            "top_platforms": ["instagram", "tiktok"],
            "avg_posts_per_week": 7
        },
        "lifestyle": {
            "avg_engagement_rate": 0.05,
            "avg_ppv_conversion": 0.08,
            "avg_arpu": 20.0,
            "top_platforms": ["instagram", "twitter"],
            "avg_posts_per_week": 4
        }
    }
    
    return benchmarks.get(niche, benchmarks["lifestyle"])




