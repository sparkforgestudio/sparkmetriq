# api/services/messaging/segmentation.py
"""
Service de segmentation pour sélectionner les cibles des campagnes.
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from api.databases.databases import get_core_db, get_bi_db
from api.schemas.message_builder import SegmentationRule, Platform


async def build_targets(
    org_id: str,
    rule: SegmentationRule,
    platform: Platform
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Construit la liste des cibles selon les règles de segmentation.
    
    Args:
        org_id: ID de l'organisation
        rule: Règle de segmentation
        platform: Plateforme cible
        
    Returns:
        Tuple (liste des cibles enrichies, nombre total)
    """
    db_core = get_core_db()
    db_bi = get_bi_db()
    
    # 1) Base: derniers interlocuteurs par plateforme
    query = {
        "org_id": org_id,
        "platform": platform
    }
    if rule.muse_id:
        query["muse_id"] = rule.muse_id
    
    # Dernier message par user_id
    pipeline = [
        {"$match": query},
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": {"user_id": "$user_id"},
            "last_msg_at": {"$first": "$timestamp"},
            "muse_id": {"$first": "$muse_id"},
            "platform": {"$first": "$platform"},
        }}
    ]
    
    users_raw = await db_core["chat_messages"].aggregate(pipeline).to_list(length=None)
    
    # 2) Filtre inactivité
    if rule.inactive_days_gte:
        cutoff = datetime.now(timezone.utc) - timedelta(days=rule.inactive_days_gte)
        users_raw = [
            u for u in users_raw 
            if u["last_msg_at"] and u["last_msg_at"] <= cutoff
        ]
    
    # 3) Enrichir avec dépenses & langue
    enriched = []
    
    for u in users_raw:
        user_ref = u["_id"]["user_id"]
        
        # Agrégation des stats de paiement depuis analytics_events (BI)
        # Note: adapter selon votre structure d'events (peut être dans payments collection aussi)
        stats_pipeline = [
            {
                "$match": {
                    "org_id": org_id,
                    "type": "payment_success",
                    "conversation_id": {"$exists": True}  # ou user_id selon votre structure
                }
            },
            {
                "$group": {
                    "_id": "$user_id",  # ou conversation_id selon votre structure
                    "total": {"$sum": {"$ifNull": ["$data.amount", {"$ifNull": ["$amount", 0]}]}},
                    "cnt": {"$sum": 1},
                    "last_purchase": {"$max": "$ts"}
                }
            },
            {
                "$match": {"_id": user_ref}
            }
        ]
        
        stats_result = await db_bi["analytics_events"].aggregate(stats_pipeline).to_list(length=1)
        
        # Alternative: chercher directement dans payments si analytics_events ne contient pas les montants
        if not stats_result:
            # Essayer de récupérer depuis payments (Core)
            payments_pipeline = [
                {
                    "$match": {
                        "org_id": org_id,
                        "muse_id": u.get("muse_id"),
                        "status": "paid"
                    }
                },
                {
                    "$group": {
                        "_id": "$muse_id",
                        "total": {"$sum": "$amount"},
                        "cnt": {"$sum": 1},
                        "last_purchase": {"$max": "$created_at"}
                    }
                }
            ]
            payments_result = await db_core["payments"].aggregate(payments_pipeline).to_list(length=1)
            if payments_result:
                total = float(payments_result[0].get("total", 0) or 0)
                cnt = int(payments_result[0].get("cnt", 0) or 0)
                avg = (total / cnt) if cnt > 0 else 0.0
                last_purchase = payments_result[0].get("last_purchase")
            else:
                total = 0.0
                cnt = 0
                avg = 0.0
                last_purchase = None
        else:
            total = float(stats_result[0].get("total", 0) or 0)
            cnt = int(stats_result[0].get("cnt", 0) or 0)
            avg = (total / cnt) if cnt > 0 else 0.0
            last_purchase = stats_result[0].get("last_purchase")
        
        # Profil utilisateur (si disponible)
        profile = await db_core["user_profiles"].find_one({
            "org_id": org_id,
            "user_ref": user_ref
        }) or {}
        
        lang = profile.get("lang")
        first_name = profile.get("first_name") or profile.get("display_name") or ""
        
        # Construire l'objet enrichi
        target = {
            "user_ref": user_ref,
            "platform": u["platform"],
            "muse_id": u.get("muse_id"),
            "last_active_at": u["last_msg_at"],
            "total_spent": total,
            "avg_spend": avg,
            "last_purchase_at": last_purchase,
            "first_name": first_name,
            "lang": lang,
        }
        
        # 4) Appliquer les filtres financiers
        if rule.min_total_spent is not None:
            if target["total_spent"] < rule.min_total_spent:
                continue
        
        if rule.language_in:
            if target["lang"] not in rule.language_in:
                continue
        
        # has_ppv_purchase => au moins 1 payment_success
        if rule.has_ppv_purchase is not None:
            has_ppv = target["avg_spend"] > 0 or target["total_spent"] > 0
            if has_ppv != rule.has_ppv_purchase:
                continue
        
        # Tags (si système de tagging disponible)
        if rule.tags_any:
            # TODO: Implémenter si système de tags existe
            # Pour l'instant, on skip cette vérification
            pass
        
        enriched.append(target)
    
    total_count = len(enriched)
    
    # Appliquer la limite si fournie
    if rule.limit:
        enriched = enriched[:rule.limit]
    
    return enriched, total_count
