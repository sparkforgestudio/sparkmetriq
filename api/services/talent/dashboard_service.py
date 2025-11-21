# api/services/talent/dashboard_service.py
"""
Service de dashboard multi-muse pour les agences.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from api.databases.databases import db

async def compute_muse_summary(tenant_id: str, muse_id: str) -> Dict[str, Any]:
    """Calcule le résumé des performances d'une muse."""
    now = datetime.now(timezone.utc)
    d7 = now - timedelta(days=7)
    d14 = now - timedelta(days=14)

    # GMV 7j
    agg = await db["payments"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "status": "confirmed",
                "ts": {"$gte": d7, "$lt": now}
            }
        },
        {
            "$group": {
                "_id": None,
                "gmv": {"$sum": "$amount"}
            }
        }
    ]).to_list(1)
    
    revenue_7d = float(agg[0]["gmv"]) if agg else 0.0

    # Taux de réponse: replies bot+op / messages entrants
    incoming = await db["chat_messages"].count_documents({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "role": "user",
        "timestamp": {"$gte": d7, "$lt": now}
    })
    
    replies = await db["chat_messages"].count_documents({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "role": {"$in": ["bot", "operator"]},
        "timestamp": {"$gte": d7, "$lt": now}
    })
    
    replies_rate = (replies / incoming) if incoming else 0.0

    # Conversion PPV approx (si tagué dans payments)
    ppv_conv = await db["payments"].count_documents({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "status": "confirmed",
        "type": "ppv",
        "ts": {"$gte": d7, "$lt": now}
    })
    
    ppv_conv_rate = ppv_conv / max(1, incoming)

    # Croissance messages 7j vs 7-14j
    prev = await db["chat_messages"].count_documents({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "role": "user",
        "timestamp": {"$gte": d14, "$lt": d7}
    })
    
    growth = ((incoming - prev) / prev) * 100 if prev > 0 else (100.0 if incoming > 0 else 0.0)

    # Déterminer le statut
    status = "ok"
    if growth < -25 or replies_rate < 0.2:
        status = "at_risk"
    if incoming == 0 and revenue_7d == 0:
        status = "inactive"

    return {
        "muse_id": muse_id,
        "revenue_7d": revenue_7d,
        "replies_rate_7d": round(replies_rate, 3),
        "ppv_conv_rate_7d": round(ppv_conv_rate, 3),
        "growth_msgs_7d": round(growth, 1),
        "status": status
    }

async def dashboard_multi_muse(tenant_id: str) -> List[Dict[str, Any]]:
    """Récupère le dashboard multi-muse."""
    muses = await db["muses"].distinct("muse_id", {"tenant_id": tenant_id})
    rows = []
    
    for m in muses:
        summary = await compute_muse_summary(tenant_id, m)
        rows.append(summary)
    
    return rows

async def get_muse_detailed_metrics(
    tenant_id: str, 
    muse_id: str, 
    days: int = 30
) -> Dict[str, Any]:
    """Récupère les métriques détaillées d'une muse."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    
    # Métriques de base
    summary = await compute_muse_summary(tenant_id, muse_id)
    
    # Métriques par plateforme
    platform_metrics = await db["chat_messages"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "timestamp": {"$gte": cutoff}
            }
        },
        {
            "$group": {
                "_id": "$platform",
                "message_count": {"$sum": 1},
                "user_messages": {
                    "$sum": {
                        "$cond": [{"$eq": ["$role", "user"]}, 1, 0]
                    }
                },
                "bot_messages": {
                    "$sum": {
                        "$cond": [{"$eq": ["$role", "bot"]}, 1, 0]
                    }
                }
            }
        }
    ]).to_list(None)
    
    # Métriques de revenus par jour
    daily_revenue = await db["payments"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "status": "confirmed",
                "ts": {"$gte": cutoff}
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$ts"
                    }
                },
                "daily_revenue": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]).to_list(None)
    
    # Métriques de threads
    thread_stats = await db["chat_threads"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "muse_id": muse_id
            }
        },
        {
            "$group": {
                "_id": None,
                "total_threads": {"$sum": 1},
                "unseen_threads": {
                    "$sum": {
                        "$cond": [{"$gt": ["$unseen_count", 0]}, 1, 0]
                    }
                },
                "escalated_threads": {
                    "$sum": {
                        "$cond": [{"$gt": ["$priority", 0]}, 1, 0]
                    }
                },
                "vip_threads": {
                    "$sum": {
                        "$cond": [{"$in": ["vip", "$tags"]}, 1, 0]
                    }
                }
            }
        }
    ]).to_list(1)
    
    thread_summary = thread_stats[0] if thread_stats else {
        "total_threads": 0,
        "unseen_threads": 0,
        "escalated_threads": 0,
        "vip_threads": 0
    }
    
    return {
        "summary": summary,
        "platform_metrics": platform_metrics,
        "daily_revenue": daily_revenue,
        "thread_stats": thread_summary,
        "period_days": days
    }

async def get_segment_metrics(
    tenant_id: str, 
    segment: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict[str, Any]:
    """Récupère les métriques par segment de muses."""
    now = datetime.now(timezone.utc)
    if not date_from:
        date_from = now - timedelta(days=30)
    if not date_to:
        date_to = now
    
    # Récupérer les muses du segment
    query = {"tenant_id": tenant_id}
    if segment:
        query["niches"] = {"$in": [segment]}
    
    muses = await db["muses"].find(query).to_list(None)
    muse_ids = [m["muse_id"] for m in muses]
    
    if not muse_ids:
        return {
            "segment": segment,
            "total_muses": 0,
            "total_revenue": 0.0,
            "avg_revenue_per_muse": 0.0,
            "total_messages": 0,
            "avg_response_rate": 0.0
        }
    
    # Métriques consolidées
    total_revenue = await db["payments"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "muse_id": {"$in": muse_ids},
                "status": "confirmed",
                "ts": {"$gte": date_from, "$lt": date_to}
            }
        },
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$amount"}
            }
        }
    ]).to_list(1)
    
    total_messages = await db["chat_messages"].count_documents({
        "tenant_id": tenant_id,
        "muse_id": {"$in": muse_ids},
        "timestamp": {"$gte": date_from, "$lt": date_to}
    })
    
    total_replies = await db["chat_messages"].count_documents({
        "tenant_id": tenant_id,
        "muse_id": {"$in": muse_ids},
        "role": {"$in": ["bot", "operator"]},
        "timestamp": {"$gte": date_from, "$lt": date_to}
    })
    
    revenue_val = float(total_revenue[0]["total"]) if total_revenue else 0.0
    response_rate = (total_replies / total_messages) if total_messages > 0 else 0.0
    
    return {
        "segment": segment,
        "total_muses": len(muse_ids),
        "total_revenue": revenue_val,
        "avg_revenue_per_muse": revenue_val / len(muse_ids) if muse_ids else 0.0,
        "total_messages": total_messages,
        "total_replies": total_replies,
        "avg_response_rate": round(response_rate, 3),
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat()
        }
    }

async def get_agency_overview(tenant_id: str) -> Dict[str, Any]:
    """Récupère la vue d'ensemble de l'agence."""
    # Compter les muses
    total_muses = await db["muses"].count_documents({"tenant_id": tenant_id})
    
    # Compter les opérateurs actifs
    active_operators = await db["operator_roles"].distinct("user_id", {"tenant_id": tenant_id})
    
    # Revenus totaux 7j
    now = datetime.now(timezone.utc)
    d7 = now - timedelta(days=7)
    
    total_revenue = await db["payments"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "status": "confirmed",
                "ts": {"$gte": d7, "$lt": now}
            }
        },
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$amount"}
            }
        }
    ]).to_list(1)
    
    # Taux de réponse global
    total_messages = await db["chat_messages"].count_documents({
        "tenant_id": tenant_id,
        "role": "user",
        "timestamp": {"$gte": d7, "$lt": now}
    })
    
    total_replies = await db["chat_messages"].count_documents({
        "tenant_id": tenant_id,
        "role": {"$in": ["bot", "operator"]},
        "timestamp": {"$gte": d7, "$lt": now}
    })
    
    # Threads totaux
    total_threads = await db["chat_threads"].count_documents({"tenant_id": tenant_id})
    escalated_threads = await db["chat_threads"].count_documents({
        "tenant_id": tenant_id,
        "priority": {"$gt": 0}
    })
    
    # Top muse performante
    top_muse = await db["payments"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "status": "confirmed",
                "ts": {"$gte": d7, "$lt": now}
            }
        },
        {
            "$group": {
                "_id": "$muse_id",
                "revenue": {"$sum": "$amount"}
            }
        },
        {
            "$sort": {"revenue": -1}
        },
        {
            "$limit": 1
        }
    ]).to_list(1)
    
    # Muses à risque
    at_risk_muses = []
    muses = await db["muses"].distinct("muse_id", {"tenant_id": tenant_id})
    
    for muse_id in muses:
        summary = await compute_muse_summary(tenant_id, muse_id)
        if summary["status"] == "at_risk":
            at_risk_muses.append(muse_id)
    
    revenue_val = float(total_revenue[0]["total"]) if total_revenue else 0.0
    response_rate = (total_replies / total_messages) if total_messages > 0 else 0.0
    
    return {
        "total_muses": total_muses,
        "active_operators": len(active_operators),
        "total_revenue_7d": revenue_val,
        "avg_response_rate": round(response_rate, 3),
        "total_threads": total_threads,
        "escalated_threads": escalated_threads,
        "top_performing_muse": top_muse[0]["_id"] if top_muse else None,
        "at_risk_muses": at_risk_muses,
        "period": "7_days"
    }

async def get_operator_performance(tenant_id: str, operator_id: str) -> Dict[str, Any]:
    """Récupère les performances d'un opérateur."""
    now = datetime.now(timezone.utc)
    d7 = now - timedelta(days=7)
    
    # Assignations de l'opérateur
    assignments = await db["muse_assignments"].find({
        "tenant_id": tenant_id,
        "operator_id": operator_id
    }).to_list(None)
    
    assigned_muses = [a["muse_id"] for a in assignments]
    
    # Messages répondu par l'opérateur
    replies_today = await db["chat_messages"].count_documents({
        "tenant_id": tenant_id,
        "muse_id": {"$in": assigned_muses},
        "role": "operator",
        "user_id": operator_id,
        "timestamp": {"$gte": d7, "$lt": now}
    })
    
    # Threads actifs
    active_threads = await db["chat_threads"].count_documents({
        "tenant_id": tenant_id,
        "muse_id": {"$in": assigned_muses},
        "unseen_count": {"$gt": 0}
    })
    
    # Temps de réponse moyen (simulé pour V1)
    avg_response_time = 15.5  # minutes
    
    # Score de performance (simulé)
    performance_score = min(100, (replies_today * 10) + (100 - active_threads))
    
    return {
        "operator_id": operator_id,
        "assigned_muses": assigned_muses,
        "total_threads": len(assigned_muses) * 10,  # Simulé
        "active_threads": active_threads,
        "replies_today": replies_today,
        "avg_response_time": avg_response_time,
        "performance_score": performance_score
    }



