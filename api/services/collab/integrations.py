# api/services/collab/integrations.py
"""
Intégrations externes pour la collaboration (ClickUp/Notion).
Stubs pour MVP - à compléter avec les vraies APIs.
"""

from typing import Dict, Any
import logging

from api.core.settings import settings

logger = logging.getLogger(__name__)


async def sync_to_clickup(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronise une tâche vers ClickUp.
    
    Args:
        task: Dictionnaire de la tâche
        
    Returns:
        Résultat de la synchronisation
    """
    if not settings.feature_collab_integrations:
        return {"ok": False, "reason": "integration_disabled"}
    
    if not settings.clickup_api_token:
        return {"ok": False, "reason": "clickup_token_not_configured"}
    
    # TODO: Implémenter l'appel réel à ClickUp API v2
    # Exemple structure:
    # - POST https://api.clickup.com/api/v2/list/{list_id}/task
    # - Headers: Authorization: {clickup_api_token}
    # - Body: {name: task.title, description: task.description, assignees: [...], due_date: task.due_at, ...}
    
    logger.info(f"[STUB] Would sync task {task.get('id')} to ClickUp")
    
    # Stub pour MVP
    return {
        "ok": True,
        "id": f"clickup:stub:{task.get('id', '123')}",
        "url": f"https://app.clickup.com/t/stub_{task.get('id', '123')}"
    }


async def sync_to_notion(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronise une tâche vers Notion.
    
    Args:
        task: Dictionnaire de la tâche
        
    Returns:
        Résultat de la synchronisation
    """
    if not settings.feature_collab_integrations:
        return {"ok": False, "reason": "integration_disabled"}
    
    if not settings.notion_api_token:
        return {"ok": False, "reason": "notion_token_not_configured"}
    
    # TODO: Implémenter l'appel réel à Notion API
    # Exemple structure:
    # - POST https://api.notion.com/v1/pages
    # - Headers: Authorization: Bearer {notion_api_token}, Notion-Version: 2022-06-28
    # - Body: {parent: {database_id: "..."}, properties: {Title: {...}, Status: {...}, ...}}
    
    logger.info(f"[STUB] Would sync task {task.get('id')} to Notion")
    
    # Stub pour MVP
    return {
        "ok": True,
        "id": f"notion:stub:{task.get('id', 'abc')}",
        "url": f"https://notion.so/stub_{task.get('id', 'abc')}"
    }



