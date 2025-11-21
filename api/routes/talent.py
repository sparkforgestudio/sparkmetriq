# api/routes/talent.py
"""
Routes FastAPI pour la Gestion Centralisée des Talents.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.core.permissions import require_role, require_operator_or_above, require_supervisor_or_above, require_lead_agent_or_above
from api.schemas.talent import (
    Thread, ThreadFilter, TagRequest, NoteIn, Note, RoleGrant,
    AssignmentIn, Assignment, AuditEvent, AuditEventIn,
    HookIn, Hook, MuseDashboardRow, SegmentQuery, ThreadSummary, OperatorStats, AgencyMetrics
)
from api.services.talent.inbox_service import (
    list_threads, tag_fan, remove_tag, add_note, list_notes, 
    escalate_thread, get_thread_details, get_thread_stats, search_threads, bulk_tag_fans
)
from api.services.talent.assignment_service import (
    grant_role, revoke_role, get_user_roles, assign_operator, unassign_operator,
    list_assignments, get_assigned_operator, get_operators_by_role, get_assignment_stats
)
from api.services.talent.audit_service import (
    log_event, log_message_event, log_tag_event, log_note_event, 
    log_escalation_event, log_role_event, log_assignment_event, log_integration_event,
    get_audit_events, get_audit_summary, export_audit_data
)
from api.services.talent.integrations_service import (
    upsert_hook, get_hook, list_hooks, delete_hook, trigger_task_creation,
    get_integration_logs, test_integration, get_integration_stats
)
from api.services.talent.dashboard_service import (
    dashboard_multi_muse, get_muse_detailed_metrics, get_segment_metrics,
    get_agency_overview, get_operator_performance
)
from api.databases.databases import db

router = APIRouter(prefix="/talent", tags=["talent"])

# === INBOX+ — Gestion des conversations ===

@router.get("/inbox", response_model=Dict[str, Any])
async def inbox_list(
    muse_id: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    """Liste les threads de conversation avec filtres."""
    require_operator_or_above(current_user)
    
    total, rows = await list_threads(
        current_user.id, 
        {
            "muse_id": muse_id, 
            "platform": platform, 
            "status": status, 
            "q": q
        }, 
        page, 
        page_size
    )
    
    return {
        "total": total, 
        "items": rows, 
        "page": page, 
        "page_size": page_size
    }

@router.get("/inbox/{muse_id}/{user_hash}", response_model=ThreadSummary)
async def get_thread_summary(
    muse_id: str,
    user_hash: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère le résumé détaillé d'un thread."""
    require_operator_or_above(current_user)
    
    thread_details = await get_thread_details(current_user.id, muse_id, user_hash)
    if not thread_details:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Récupérer l'opérateur assigné
    assigned_operator = await get_assigned_operator(current_user.id, muse_id, thread_details["platform"])
    
    return ThreadSummary(
        thread=Thread(**thread_details),
        message_count=len(thread_details.get("messages", [])),
        last_activity=thread_details["last_ts"],
        assigned_operator=assigned_operator,
        notes_count=len(thread_details.get("notes", [])),
        tags_count=len(thread_details.get("tags", []))
    )

@router.get("/inbox/search", response_model=List[Thread])
async def search_inbox(
    q: str = Query(..., min_length=2),
    muse_id: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    """Recherche dans les threads."""
    require_operator_or_above(current_user)
    
    threads = await search_threads(current_user.id, q, muse_id, platform, limit)
    return [Thread(**thread) for thread in threads]

# === TAGGING & NOTES ===

@router.post("/fans/tag", response_model=dict)
async def add_tag(
    payload: TagRequest, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Ajoute un tag à un fan."""
    require_operator_or_above(current_user)
    
    await tag_fan(current_user.id, payload.muse_id, payload.user_hash, payload.tag)
    await log_tag_event(current_user.id, current_user.id, payload.muse_id, payload.user_hash, payload.tag)
    
    return {"ok": True}

@router.delete("/fans/tag", response_model=dict)
async def remove_tag_endpoint(
    payload: TagRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Retire un tag d'un fan."""
    require_operator_or_above(current_user)
    
    await remove_tag(current_user.id, payload.muse_id, payload.user_hash, payload.tag)
    await log_tag_event(current_user.id, current_user.id, payload.muse_id, payload.user_hash, payload.tag, "tag_removed")
    
    return {"ok": True}

@router.post("/fans/tag/bulk", response_model=dict)
async def bulk_tag_fans_endpoint(
    muse_id: str,
    user_hashes: List[str],
    tag: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Applique un tag à plusieurs fans."""
    require_operator_or_above(current_user)
    
    await bulk_tag_fans(current_user.id, muse_id, user_hashes, tag)
    await log_event(
        current_user.id, 
        current_user.id, 
        "bulk_tag_added", 
        muse_id=muse_id, 
        meta={"tag": tag, "count": len(user_hashes)}
    )
    
    return {"ok": True, "tagged_count": len(user_hashes)}

@router.post("/fans/note", response_model=dict)
async def write_note(
    payload: NoteIn, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Ajoute une note à un fan."""
    require_operator_or_above(current_user)
    
    note_id = await add_note(current_user.id, current_user.id, payload.muse_id, payload.user_hash, payload.text)
    await log_note_event(current_user.id, current_user.id, payload.muse_id, payload.user_hash, note_id)
    
    return {"id": note_id}

@router.get("/fans/notes", response_model=List[Note])
async def get_notes(
    muse_id: str, 
    user_hash: str, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère les notes d'un fan."""
    require_operator_or_above(current_user)
    
    rows = await list_notes(current_user.id, muse_id, user_hash)
    return [Note(**r) for r in rows]

# === ESCALADE ===

@router.post("/inbox/escalate", response_model=dict)
async def escalate(
    muse_id: str, 
    user_hash: str, 
    level: int = Query(1, ge=1, le=5),
    reason: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Escalade un thread."""
    require_operator_or_above(current_user)
    
    await escalate_thread(current_user.id, muse_id, user_hash, level, reason)
    await log_escalation_event(current_user.id, current_user.id, muse_id, user_hash, level, reason)
    
    return {"ok": True}

# === RÔLES & ASSIGNATIONS ===

@router.post("/roles/grant", response_model=dict)
async def roles_grant(
    payload: RoleGrant, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Accorde un rôle à un utilisateur."""
    require_lead_agent_or_above(current_user)
    
    await grant_role(current_user.id, payload.user_id, payload.role)
    await log_role_event(current_user.id, current_user.id, payload.user_id, payload.role)
    
    return {"ok": True}

@router.delete("/roles/revoke", response_model=dict)
async def roles_revoke(
    payload: RoleGrant,
    current_user: UserResponse = Depends(get_current_user)
):
    """Révoque un rôle d'un utilisateur."""
    require_lead_agent_or_above(current_user)
    
    await revoke_role(current_user.id, payload.user_id, payload.role)
    await log_role_event(current_user.id, current_user.id, payload.user_id, payload.role, "role_revoked")
    
    return {"ok": True}

@router.get("/roles/{user_id}", response_model=List[str])
async def get_user_roles_endpoint(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère les rôles d'un utilisateur."""
    require_supervisor_or_above(current_user)
    
    roles = await get_user_roles(current_user.id, user_id)
    return roles

@router.post("/assignments", response_model=dict)
async def assignment_add(
    payload: AssignmentIn, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Assigne un opérateur à une muse pour une plateforme."""
    require_supervisor_or_above(current_user)
    
    assignment_id = await assign_operator(current_user.id, payload.muse_id, payload.platform, payload.operator_id)
    await log_assignment_event(current_user.id, current_user.id, payload.muse_id, payload.platform, payload.operator_id)
    
    return {"id": assignment_id}

@router.delete("/assignments", response_model=dict)
async def assignment_remove(
    muse_id: str,
    platform: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Retire l'assignation d'un opérateur."""
    require_supervisor_or_above(current_user)
    
    await unassign_operator(current_user.id, muse_id, platform)
    await log_assignment_event(current_user.id, current_user.id, muse_id, platform, None, "assignment_removed")
    
    return {"ok": True}

@router.get("/assignments", response_model=List[Assignment])
async def assignments_list(
    muse_id: Optional[str] = None,
    operator_id: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Liste les assignations."""
    require_operator_or_above(current_user)
    
    rows = await list_assignments(current_user.id, muse_id, operator_id)
    return [Assignment(**r) for r in rows]

@router.get("/assignments/stats", response_model=dict)
async def assignments_stats(current_user: UserResponse = Depends(get_current_user)):
    """Récupère les statistiques des assignations."""
    require_supervisor_or_above(current_user)
    
    stats = await get_assignment_stats(current_user.id)
    return stats

# === AUDIT TRAIL ===

@router.get("/audit", response_model=List[AuditEvent])
async def audit_list(
    muse_id: Optional[str] = None,
    user_hash: Optional[str] = None,
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(500, ge=1, le=1000),
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère les événements d'audit."""
    require_supervisor_or_above(current_user)
    
    events = await get_audit_events(
        current_user.id, muse_id, user_hash, actor_id, action, date_from, date_to, limit
    )
    return [AuditEvent(**event) for event in events]

@router.get("/audit/summary", response_model=dict)
async def audit_summary(
    muse_id: Optional[str] = None,
    days: int = Query(7, ge=1, le=365),
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère le résumé des événements d'audit."""
    require_supervisor_or_above(current_user)
    
    summary = await get_audit_summary(current_user.id, muse_id, days)
    return summary

@router.get("/audit/export", response_model=dict)
async def audit_export(
    format: str = Query("json"),
    muse_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Exporte les données d'audit."""
    require_lead_agent_or_above(current_user)
    
    export_data = await export_audit_data(current_user.id, format, muse_id, date_from, date_to)
    return export_data

# === INTÉGRATIONS ===

@router.post("/integrations/hooks", response_model=dict)
async def upsert_integration(
    hook: HookIn, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Enregistre ou met à jour une intégration."""
    require_lead_agent_or_above(current_user)
    
    await upsert_hook(current_user.id, hook.provider, hook.config)
    await log_integration_event(current_user.id, current_user.id, hook.provider, "integration_upserted")
    
    return {"ok": True}

@router.get("/integrations/hooks", response_model=List[Hook])
async def list_integrations(current_user: UserResponse = Depends(get_current_user)):
    """Liste les intégrations configurées."""
    require_lead_agent_or_above(current_user)
    
    hooks = await list_hooks(current_user.id)
    return [Hook(**hook) for hook in hooks]

@router.delete("/integrations/hooks/{provider}", response_model=dict)
async def delete_integration(
    provider: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Supprime une intégration."""
    require_lead_agent_or_above(current_user)
    
    await delete_hook(current_user.id, provider)
    await log_integration_event(current_user.id, current_user.id, provider, "integration_deleted")
    
    return {"ok": True}

@router.post("/integrations/test/{provider}", response_model=dict)
async def test_integration_endpoint(
    provider: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Teste une intégration."""
    require_lead_agent_or_above(current_user)
    
    result = await test_integration(current_user.id, provider)
    return result

@router.post("/integrations/create_task", response_model=dict)
async def create_task(
    muse_id: str, 
    title: str, 
    description: str,
    priority: str = Query("medium"),
    due_date: Optional[datetime] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Crée une tâche dans l'outil externe."""
    require_operator_or_above(current_user)
    
    result = await trigger_task_creation(current_user.id, muse_id, title, description, priority, due_date)
    await log_integration_event(
        current_user.id, 
        current_user.id, 
        result.get("provider", "unknown"), 
        "task_created",
        {"muse_id": muse_id, "title": title}
    )
    
    return result

@router.get("/integrations/logs", response_model=List[dict])
async def integration_logs(
    provider: Optional[str] = None,
    muse_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère les logs des intégrations."""
    require_supervisor_or_above(current_user)
    
    logs = await get_integration_logs(current_user.id, provider, muse_id, limit)
    return logs

@router.get("/integrations/stats", response_model=dict)
async def integration_stats(current_user: UserResponse = Depends(get_current_user)):
    """Récupère les statistiques des intégrations."""
    require_supervisor_or_above(current_user)
    
    stats = await get_integration_stats(current_user.id)
    return stats

# === DASHBOARD MULTI-MUSE ===

@router.get("/dashboard", response_model=List[MuseDashboardRow])
async def dashboard(current_user: UserResponse = Depends(get_current_user)):
    """Récupère le dashboard multi-muse."""
    require_role(current_user, ["strategist", "supervisor", "lead_agent", "admin"])
    
    rows = await dashboard_multi_muse(current_user.id)
    return [MuseDashboardRow(**r) for r in rows]

@router.get("/dashboard/agency", response_model=AgencyMetrics)
async def agency_overview(current_user: UserResponse = Depends(get_current_user)):
    """Récupère la vue d'ensemble de l'agence."""
    require_role(current_user, ["supervisor", "lead_agent", "admin"])
    
    overview = await get_agency_overview(current_user.id)
    return AgencyMetrics(**overview)

@router.get("/dashboard/muse/{muse_id}", response_model=dict)
async def muse_detailed_metrics(
    muse_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère les métriques détaillées d'une muse."""
    require_operator_or_above(current_user)
    
    metrics = await get_muse_detailed_metrics(current_user.id, muse_id, days)
    return metrics

@router.get("/dashboard/segment", response_model=dict)
async def segment_metrics(
    segment: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère les métriques par segment."""
    require_role(current_user, ["strategist", "supervisor", "lead_agent", "admin"])
    
    metrics = await get_segment_metrics(current_user.id, segment, date_from, date_to)
    return metrics

@router.get("/dashboard/operator/{operator_id}", response_model=OperatorStats)
async def operator_performance(
    operator_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère les performances d'un opérateur."""
    require_supervisor_or_above(current_user)
    
    performance = await get_operator_performance(current_user.id, operator_id)
    return OperatorStats(**performance)

# === STATISTIQUES GÉNÉRALES ===

@router.get("/stats/inbox", response_model=dict)
async def inbox_stats(
    muse_id: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupère les statistiques de l'inbox."""
    require_operator_or_above(current_user)
    
    stats = await get_thread_stats(current_user.id, muse_id)
    return stats
