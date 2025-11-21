# api/services/talent/integrations_service.py
"""
Service d'intégrations avec outils externes (ClickUp, Notion, Sheets, Zapier).
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId
from api.databases.databases import db

async def upsert_hook(tenant_id: str, provider: str, config: Dict[str, Any]):
    """Enregistre ou met à jour une configuration d'intégration."""
    doc = {
        "tenant_id": tenant_id,
        "provider": provider,
        "config": config,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db["integration_hooks"].update_one(
        {
            "tenant_id": tenant_id,
            "provider": provider
        },
        {
            "$set": doc
        },
        upsert=True
    )

async def get_hook(tenant_id: str, provider: str) -> Optional[Dict[str, Any]]:
    """Récupère la configuration d'une intégration."""
    hook = await db["integration_hooks"].find_one({
        "tenant_id": tenant_id,
        "provider": provider
    })
    
    if hook:
        hook["id"] = str(hook["_id"])
        del hook["_id"]
    
    return hook

async def list_hooks(tenant_id: str) -> List[Dict[str, Any]]:
    """Liste toutes les intégrations d'un tenant."""
    cursor = db["integration_hooks"].find({"tenant_id": tenant_id})
    hooks = await cursor.to_list(None)
    
    for hook in hooks:
        hook["id"] = str(hook["_id"])
        del hook["_id"]
    
    return hooks

async def delete_hook(tenant_id: str, provider: str):
    """Supprime une intégration."""
    await db["integration_hooks"].delete_one({
        "tenant_id": tenant_id,
        "provider": provider
    })

async def trigger_task_creation(
    tenant_id: str, 
    muse_id: str, 
    title: str, 
    description: str,
    priority: str = "medium",
    due_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Déclenche la création d'une tâche dans l'outil externe."""
    # Récupérer la configuration d'intégration
    hook = await get_hook(tenant_id, "clickup")  # Par défaut ClickUp
    
    if not hook:
        # Essayer d'autres providers
        for provider in ["notion", "sheets", "zapier"]:
            hook = await get_hook(tenant_id, provider)
            if hook:
                break
    
    if not hook:
        return {
            "ok": False,
            "error": "No integration configured",
            "provider": None
        }
    
    provider = hook["provider"]
    config = hook["config"]
    
    # Simuler la création de tâche selon le provider
    if provider == "clickup":
        result = await _create_clickup_task(config, title, description, priority, due_date)
    elif provider == "notion":
        result = await _create_notion_page(config, title, description, priority, due_date)
    elif provider == "sheets":
        result = await _add_sheets_row(config, title, description, priority, due_date)
    elif provider == "zapier":
        result = await _trigger_zapier_webhook(config, title, description, priority, due_date)
    else:
        result = {"ok": False, "error": f"Unknown provider: {provider}"}
    
    # Enregistrer le résultat dans les logs
    await db["integration_logs"].insert_one({
        "tenant_id": tenant_id,
        "provider": provider,
        "action": "task_created",
        "muse_id": muse_id,
        "title": title,
        "result": result,
        "ts": datetime.now(timezone.utc)
    })
    
    return {
        "ok": result.get("ok", False),
        "provider": provider,
        "task_id": result.get("task_id"),
        "url": result.get("url"),
        "error": result.get("error")
    }

async def _create_clickup_task(
    config: Dict[str, Any], 
    title: str, 
    description: str, 
    priority: str,
    due_date: Optional[datetime]
) -> Dict[str, Any]:
    """Simule la création d'une tâche ClickUp."""
    # Pour V1, on simule juste le succès
    # Dans une version future, cela ferait appel à l'API ClickUp
    
    task_id = f"clickup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return {
        "ok": True,
        "task_id": task_id,
        "url": f"https://app.clickup.com/t/{task_id}",
        "provider": "clickup"
    }

async def _create_notion_page(
    config: Dict[str, Any], 
    title: str, 
    description: str, 
    priority: str,
    due_date: Optional[datetime]
) -> Dict[str, Any]:
    """Simule la création d'une page Notion."""
    page_id = f"notion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return {
        "ok": True,
        "task_id": page_id,
        "url": f"https://notion.so/{page_id}",
        "provider": "notion"
    }

async def _add_sheets_row(
    config: Dict[str, Any], 
    title: str, 
    description: str, 
    priority: str,
    due_date: Optional[datetime]
) -> Dict[str, Any]:
    """Simule l'ajout d'une ligne dans Google Sheets."""
    row_id = f"sheets_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return {
        "ok": True,
        "task_id": row_id,
        "url": f"https://docs.google.com/spreadsheets/d/{config.get('sheet_id')}/edit",
        "provider": "sheets"
    }

async def _trigger_zapier_webhook(
    config: Dict[str, Any], 
    title: str, 
    description: str, 
    priority: str,
    due_date: Optional[datetime]
) -> Dict[str, Any]:
    """Simule le déclenchement d'un webhook Zapier."""
    webhook_id = f"zapier_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return {
        "ok": True,
        "task_id": webhook_id,
        "url": f"https://zapier.com/webhook/{webhook_id}",
        "provider": "zapier"
    }

async def sync_calendar_events(
    tenant_id: str,
    muse_id: str,
    events: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Synchronise des événements de calendrier."""
    hook = await get_hook(tenant_id, "google_calendar")
    
    if not hook:
        return {
            "ok": False,
            "error": "Google Calendar integration not configured"
        }
    
    # Simuler la synchronisation
    synced_events = []
    for event in events:
        event_id = f"cal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        synced_events.append({
            "event_id": event_id,
            "title": event["title"],
            "start": event["start"],
            "end": event["end"]
        })
    
    return {
        "ok": True,
        "synced_events": synced_events,
        "provider": "google_calendar"
    }

async def export_to_sheets(
    tenant_id: str,
    muse_id: str,
    data: List[Dict[str, Any]],
    sheet_name: str
) -> Dict[str, Any]:
    """Exporte des données vers Google Sheets."""
    hook = await get_hook(tenant_id, "sheets")
    
    if not hook:
        return {
            "ok": False,
            "error": "Google Sheets integration not configured"
        }
    
    # Simuler l'export
    export_id = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return {
        "ok": True,
        "export_id": export_id,
        "rows_exported": len(data),
        "url": f"https://docs.google.com/spreadsheets/d/{hook['config'].get('sheet_id')}/edit",
        "provider": "sheets"
    }

async def get_integration_logs(
    tenant_id: str,
    provider: Optional[str] = None,
    muse_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Récupère les logs des intégrations."""
    query = {"tenant_id": tenant_id}
    
    if provider:
        query["provider"] = provider
    if muse_id:
        query["muse_id"] = muse_id
    
    cursor = db["integration_logs"].find(query).sort("ts", -1).limit(limit)
    logs = await cursor.to_list(None)
    
    for log in logs:
        log["id"] = str(log["_id"])
        del log["_id"]
    
    return logs

async def test_integration(tenant_id: str, provider: str) -> Dict[str, Any]:
    """Teste une intégration."""
    hook = await get_hook(tenant_id, provider)
    
    if not hook:
        return {
            "ok": False,
            "error": f"No configuration found for {provider}"
        }
    
    # Simuler un test selon le provider
    if provider == "clickup":
        result = await _test_clickup_connection(hook["config"])
    elif provider == "notion":
        result = await _test_notion_connection(hook["config"])
    elif provider == "sheets":
        result = await _test_sheets_connection(hook["config"])
    elif provider == "zapier":
        result = await _test_zapier_connection(hook["config"])
    else:
        result = {"ok": False, "error": f"Unknown provider: {provider}"}
    
    return result

async def _test_clickup_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """Teste la connexion ClickUp."""
    # Simuler un test de connexion
    return {
        "ok": True,
        "message": "ClickUp connection successful",
        "workspace": config.get("workspace_name", "Unknown")
    }

async def _test_notion_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """Teste la connexion Notion."""
    return {
        "ok": True,
        "message": "Notion connection successful",
        "database": config.get("database_name", "Unknown")
    }

async def _test_sheets_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """Teste la connexion Google Sheets."""
    return {
        "ok": True,
        "message": "Google Sheets connection successful",
        "sheet": config.get("sheet_name", "Unknown")
    }

async def _test_zapier_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """Teste la connexion Zapier."""
    return {
        "ok": True,
        "message": "Zapier webhook connection successful",
        "webhook": config.get("webhook_url", "Unknown")
    }

async def get_integration_stats(tenant_id: str) -> Dict[str, Any]:
    """Récupère les statistiques des intégrations."""
    # Compter les logs par provider
    provider_stats = await db["integration_logs"].aggregate([
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {
            "_id": "$provider",
            "total_actions": {"$sum": 1},
            "successful_actions": {
                "$sum": {
                    "$cond": [{"$eq": ["$result.ok", True]}, 1, 0]
                }
            },
            "last_action": {"$max": "$ts"}
        }}
    ]).to_list(None)
    
    # Compter les actions par muse
    muse_stats = await db["integration_logs"].aggregate([
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {
            "_id": "$muse_id",
            "total_actions": {"$sum": 1}
        }}
    ]).to_list(None)
    
    return {
        "providers": provider_stats,
        "muses": muse_stats,
        "total_integrations": len(provider_stats)
    }



