# api/services/scheduler/planner_service.py
"""
Service de planification et gestion des drafts.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId
from api.databases.databases import db
from api.schemas.scheduler import DraftIn, Draft

def _utc(dt: datetime) -> datetime:
    """Convertit une datetime en UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

async def create_draft(tenant_id: str, payload: DraftIn) -> str:
    """Crée un nouveau draft programmé."""
    now = datetime.now(timezone.utc)
    doc = {
        "tenant_id": tenant_id,
        "status": "scheduled",
        "job_id": None,
        "created_at": now,
        "updated_at": now,
        **payload.model_dump(),
        "scheduled_at": _utc(payload.scheduled_at),
    }
    r = await db["scheduled_drafts"].insert_one(doc)
    return str(r.inserted_id)

async def get_draft(tenant_id: str, draft_id: str) -> Optional[Dict[str, Any]]:
    """Récupère un draft par ID."""
    return await db["scheduled_drafts"].find_one({"_id": ObjectId(draft_id), "tenant_id": tenant_id})

async def list_drafts(tenant_id: str, muse_id: Optional[str]=None, status: Optional[str]=None, date_from: Optional[datetime]=None, date_to: Optional[datetime]=None) -> List[Dict[str, Any]]:
    """Liste les drafts avec filtres."""
    q = {"tenant_id": tenant_id}
    if muse_id: 
        q["muse_id"] = muse_id
    if status: 
        q["status"] = status
    if date_from or date_to:
        q["scheduled_at"] = {}
        if date_from: 
            q["scheduled_at"]["$gte"] = _utc(date_from)
        if date_to: 
            q["scheduled_at"]["$lte"] = _utc(date_to)
    
    cur = db["scheduled_drafts"].find(q).sort("scheduled_at", 1)
    return await cur.to_list(None)

async def update_draft(tenant_id: str, draft_id: str, updates: Dict[str, Any]) -> bool:
    """Met à jour un draft."""
    updates["updated_at"] = datetime.now(timezone.utc)
    if "scheduled_at" in updates:
        updates["scheduled_at"] = _utc(updates["scheduled_at"])
    
    res = await db["scheduled_drafts"].update_one(
        {"_id": ObjectId(draft_id), "tenant_id": tenant_id},
        {"$set": updates}
    )
    return res.modified_count == 1

async def delete_draft(tenant_id: str, draft_id: str) -> bool:
    """Supprime un draft."""
    res = await db["scheduled_drafts"].delete_one({"_id": ObjectId(draft_id), "tenant_id": tenant_id})
    return res.deleted_count == 1

async def generate_weekly_plan(tenant_id: str, muse_id: str, start_day: datetime, persona_tone: str, objective: str) -> List[str]:
    """
    Génère 3 à 5 drafts répartis sur la semaine (Lun/Me/Ven) avec des formats variables.
    """
    start_day = _utc(start_day).replace(hour=10, minute=0, second=0, microsecond=0)
    days = [start_day, start_day + timedelta(days=2), start_day + timedelta(days=4)]
    platforms = ["instagram", "twitter", "reddit"]
    
    # Générer des thèmes via IA
    from api.services.scheduler.ai_copy_service import generate_weekly_themes
    themes = await generate_weekly_themes(muse_id, persona_tone, objective)

    ids = []
    for i, day in enumerate(days):
        theme = themes[i] if i < len(themes) else f"Weekly auto-plan teaser #{i+1}"
        
        payload = DraftIn(
            platform=platforms[i % len(platforms)],
            muse_id=muse_id,
            title=theme,
            caption=f"{theme} - Auto-generated content",
            scheduled_at=day,
            tone=persona_tone,
            objective=objective,
            hashtags=["#weekly", "#auto", "#content"],
            emojis=["🔥", "💋"]
        )
        draft_id = await create_draft(tenant_id, payload)
        ids.append(draft_id)
    
    return ids

async def get_optimal_posting_times(platform: str, muse_id: str) -> List[str]:
    """Retourne les heures optimales de publication (mock pour V1)."""
    optimal_times = {
        "instagram": ["09:00", "12:00", "15:00", "18:00"],
        "twitter": ["08:00", "12:00", "17:00", "20:00"],
        "tiktok": ["06:00", "10:00", "19:00", "22:00"],
        "reddit": ["09:00", "13:00", "17:00", "21:00"],
        "telegram": ["08:00", "12:00", "18:00", "22:00"],
        "onlyfans": ["10:00", "14:00", "19:00", "23:00"],
        "threads": ["09:00", "13:00", "17:00", "20:00"]
    }
    return optimal_times.get(platform, ["10:00", "14:00", "18:00", "22:00"])

async def get_content_calendar(tenant_id: str, muse_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Génère un calendrier de contenu pour une période donnée."""
    drafts = await list_drafts(tenant_id, muse_id=muse_id, date_from=start_date, date_to=end_date)
    
    calendar = {}
    for draft in drafts:
        date_key = draft["scheduled_at"].strftime("%Y-%m-%d")
        if date_key not in calendar:
            calendar[date_key] = []
        
        calendar[date_key].append({
            "id": str(draft["_id"]),
            "platform": draft["platform"],
            "title": draft.get("title"),
            "caption": draft.get("caption"),
            "scheduled_at": draft["scheduled_at"].isoformat(),
            "status": draft["status"]
        })
    
    return calendar



