# api/services/scheduler/recycle_service.py
"""
Service de recyclage intelligent de contenu.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from api.databases.databases import db
from api.schemas.scheduler import DraftIn

async def pick_top_content(tenant_id: str, muse_id: str, selection: str, lookback_days: int, limit: int=3) -> List[Dict[str, Any]]:
    """Sélectionne le meilleur contenu selon les critères."""
    since = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    
    # Récupérer les publications récentes
    cur = db["publish_logs"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "ts": {"$gte": since},
        "status": "published"
    }).sort("ts", -1).limit(100)
    
    rows = await cur.to_list(None)
    
    # Calculer les scores selon la sélection
    scored = []
    for r in rows:
        metrics = (r.get("connector_result") or {}).get("metrics", {})
        score = 0.0
        
        if selection == "top_by_ctr":
            score = float(metrics.get("ctr", 0.0))
        elif selection == "top_by_ppv":
            score = float(metrics.get("ppv_paid", 0.0))
        elif selection == "top_by_views":
            score = float(metrics.get("views", 0.0))
        elif selection == "top_by_engagement":
            # Score composite: likes + comments + shares
            likes = float(metrics.get("likes", 0.0))
            comments = float(metrics.get("comments", 0.0))
            shares = float(metrics.get("shares", 0.0))
            score = likes + (comments * 2) + (shares * 3)
        
        scored.append((score, r))
    
    # Trier par score décroissant
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:limit]]

async def schedule_recycle(tenant_id: str, muse_id: str, policy: Dict[str, Any]) -> List[str]:
    """Programme le recyclage de contenu selon une politique."""
    top = await pick_top_content(
        tenant_id=tenant_id,
        muse_id=muse_id,
        selection=policy.get("selection","top_by_ctr"),
        lookback_days=int(policy.get("lookback_days", 30)),
        limit=int(policy.get("max_per_week", 3))
    )
    
    # Reformat multi-plateformes
    ids = []
    offset_h = 6
    
    from api.services.scheduler.planner_service import create_draft
    
    for i, row in enumerate(top):
        ref_caption = "Recycle: " + row.get("connector_result", {}).get("caption","")
        original_platform = row.get("platform", "instagram")
        
        # Adapter le contenu pour chaque plateforme cible
        for target_platform in policy.get("reformat", ["twitter","reddit","instagram"]):
            adapted_caption = await _adapt_content_for_platform(
                ref_caption, 
                original_platform, 
                target_platform
            )
            
            payload = DraftIn(
                platform=target_platform,
                muse_id=muse_id,
                caption=adapted_caption[:2200],  # Limiter la longueur
                scheduled_at=(datetime.now(timezone.utc) + timedelta(hours=1 + i*offset_h)),
                tone="flirty",
                objective="conversion",
                hashtags=["#recycle", "#throwback"],
                emojis=["🔄", "💫"],
                meta={
                    "recycled_from": str(row.get("_id")),
                    "original_platform": original_platform,
                    "recycle_policy": policy.get("name", "default")
                }
            )
            
            draft_id = await create_draft(tenant_id, payload)
            ids.append(draft_id)
    
    return ids

async def _adapt_content_for_platform(content: str, from_platform: str, to_platform: str) -> str:
    """Adapte le contenu d'une plateforme à une autre."""
    # Règles d'adaptation simples
    adaptations = {
        "instagram_to_twitter": lambda x: x[:280],  # Twitter limite
        "twitter_to_instagram": lambda x: x + " #instagram #content",
        "reddit_to_instagram": lambda x: x.replace("[", "").replace("]", ""),  # Supprimer les liens Reddit
        "instagram_to_reddit": lambda x: x.replace("#", ""),  # Supprimer les hashtags
    }
    
    key = f"{from_platform}_to_{to_platform}"
    if key in adaptations:
        return adaptations[key](content)
    
    # Adaptation par défaut
    if to_platform == "twitter":
        return content[:280]
    elif to_platform == "reddit":
        return content.replace("#", "")
    else:
        return content

async def create_recycle_policy(tenant_id: str, muse_id: str, policy: Dict[str, Any]) -> str:
    """Crée une politique de recyclage."""
    doc = {
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        **policy
    }
    
    result = await db["recycle_policies"].insert_one(doc)
    return str(result.inserted_id)

async def get_recycle_policies(tenant_id: str, muse_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Récupère les politiques de recyclage."""
    query = {"tenant_id": tenant_id}
    if muse_id:
        query["muse_id"] = muse_id
    
    cursor = db["recycle_policies"].find(query).sort("created_at", -1)
    return await cursor.to_list(None)

async def update_recycle_policy(tenant_id: str, policy_id: str, updates: Dict[str, Any]) -> bool:
    """Met à jour une politique de recyclage."""
    updates["updated_at"] = datetime.now(timezone.utc)
    
    result = await db["recycle_policies"].update_one(
        {"_id": policy_id, "tenant_id": tenant_id},
        {"$set": updates}
    )
    
    return result.modified_count == 1

async def delete_recycle_policy(tenant_id: str, policy_id: str) -> bool:
    """Supprime une politique de recyclage."""
    result = await db["recycle_policies"].delete_one({"_id": policy_id, "tenant_id": tenant_id})
    return result.deleted_count == 1

async def get_recycle_analytics(tenant_id: str, muse_id: str, days: int = 30) -> Dict[str, Any]:
    """Analyse les performances du recyclage."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Récupérer les drafts recyclés
    recycled_drafts = await db["scheduled_drafts"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "meta.recycled_from": {"$exists": True},
        "created_at": {"$gte": since}
    }).to_list(None)
    
    # Analyser les performances
    total_recycled = len(recycled_drafts)
    published_recycled = len([d for d in recycled_drafts if d["status"] == "published"])
    
    # Calculer les métriques moyennes
    avg_performance = {
        "views": 0,
        "likes": 0,
        "comments": 0,
        "ctr": 0
    }
    
    if published_recycled > 0:
        # Récupérer les logs de publication pour les drafts recyclés publiés
        published_ids = [str(d["_id"]) for d in recycled_drafts if d["status"] == "published"]
        
        logs = await db["publish_logs"].find({
            "tenant_id": tenant_id,
            "draft_id": {"$in": published_ids}
        }).to_list(None)
        
        if logs:
            metrics = [log.get("connector_result", {}).get("metrics", {}) for log in logs]
            avg_performance = {
                "views": sum(float(m.get("views", 0)) for m in metrics) / len(metrics),
                "likes": sum(float(m.get("likes", 0)) for m in metrics) / len(metrics),
                "comments": sum(float(m.get("comments", 0)) for m in metrics) / len(metrics),
                "ctr": sum(float(m.get("ctr", 0)) for m in metrics) / len(metrics)
            }
    
    return {
        "total_recycled": total_recycled,
        "published_recycled": published_recycled,
        "success_rate": published_recycled / total_recycled if total_recycled > 0 else 0,
        "avg_performance": avg_performance,
        "period_days": days
    }



