# api/services/scheduler/publish_service.py
"""
Service d'exécution des publications programmées.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId
from api.databases.databases import db
from api.services.scheduler.ai_copy_service import generate_preview

async def execute_publish(draft_id: str, tenant_id: str) -> Dict[str, Any]:
    """Exécute la publication d'un draft."""
    draft = await db["scheduled_drafts"].find_one({"_id": ObjectId(draft_id), "tenant_id": tenant_id})
    if not draft:
        return {"ok": False, "reason": "draft_not_found"}

    platform = draft["platform"]
    
    # Récupérer le connecteur approprié
    connector = await _get_connector(platform)
    if not connector:
        await _mark_failed(draft, "no_connector")
        return {"ok": False, "reason": "no_connector"}

    # Générer le contenu via IA si nécessaire
    caption = draft.get("caption")
    if not caption:
        preview = await generate_preview(
            platform=platform,
            muse_id=draft["muse_id"],
            tone=draft.get("tone") or "flirty",
            objective=draft.get("objective") or "teasing",
            language=draft.get("meta",{}).get("language","en"),
            user_prompt=draft.get("title") or "Sexy teaser"
        )
        caption = preview.get("caption","")

    media = draft.get("media", [])
    link_out = draft.get("link_out")

    # Envoi via le connecteur
    try:
        result = await connector.send_post(
            muse_id=draft["muse_id"],
            caption=caption,
            media=media,
            link_out=link_out,
            story=bool(draft.get("story")),
            reel=bool(draft.get("reel")),
            nsfw_filter=bool(draft.get("nsfw_filter")),
        )
    except Exception as e:
        await _mark_failed(draft, f"connector_error: {str(e)}")
        return {"ok": False, "reason": f"connector_error: {str(e)}"}

    # Enregistrer le log de publication
    await db["publish_logs"].insert_one({
        "tenant_id": tenant_id,
        "muse_id": draft["muse_id"],
        "platform": platform,
        "status": "published" if result.get("ok") else "failed",
        "ts": datetime.now(timezone.utc),
        "draft_id": str(draft["_id"]),
        "connector_result": result,
        "caption": caption,
        "media_count": len(media)
    })

    # Mettre à jour le statut du draft
    await db["scheduled_drafts"].update_one(
        {"_id": draft["_id"]},
        {"$set":{
            "status": "published" if result.get("ok") else "failed",
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {"ok": bool(result.get("ok")), "result": result}

async def _get_connector(platform: str):
    """Récupère le connecteur pour une plateforme donnée."""
    try:
        from api.services.content_distributor.connectors.registry import get
        return get(platform)
    except ImportError:
        # Fallback si le registry n'existe pas encore
        return _mock_connector(platform)

def _mock_connector(platform: str):
    """Connecteur mock pour les tests."""
    class MockConnector:
        async def send_post(self, *, muse_id: str, caption: str, media: list, link_out: str, story: bool, reel: bool, nsfw_filter: bool) -> dict:
            return {
                "ok": True,
                "post_id": f"mock_{platform}_{muse_id}",
                "url": f"https://{platform}.com/posts/mock_{muse_id}",
                "metrics": {
                    "views": 100,
                    "likes": 10,
                    "comments": 2,
                    "ctr": 0.05
                }
            }
    return MockConnector()

async def _mark_failed(draft: Dict[str, Any], reason: str):
    """Marque un draft comme échoué."""
    await db["publish_logs"].insert_one({
        "tenant_id": draft["tenant_id"],
        "muse_id": draft["muse_id"],
        "platform": draft["platform"],
        "status": "failed",
        "reason": reason,
        "ts": datetime.now(timezone.utc),
        "draft_id": str(draft["_id"]),
    })
    
    await db["scheduled_drafts"].update_one(
        {"_id": draft["_id"]},
        {"$set":{
            "status": "failed",
            "updated_at": datetime.now(timezone.utc)
        }}
    )

async def retry_failed_publish(draft_id: str, tenant_id: str) -> Dict[str, Any]:
    """Relance une publication échouée."""
    draft = await db["scheduled_drafts"].find_one({"_id": ObjectId(draft_id), "tenant_id": tenant_id})
    if not draft:
        return {"ok": False, "reason": "draft_not_found"}
    
    if draft["status"] != "failed":
        return {"ok": False, "reason": "draft_not_failed"}
    
    # Réessayer la publication
    return await execute_publish(draft_id, tenant_id)

async def get_publish_history(tenant_id: str, muse_id: Optional[str] = None, platform: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Récupère l'historique des publications."""
    query = {"tenant_id": tenant_id}
    if muse_id:
        query["muse_id"] = muse_id
    if platform:
        query["platform"] = platform
    
    cursor = db["publish_logs"].find(query).sort("ts", -1).limit(limit)
    return await cursor.to_list(None)
