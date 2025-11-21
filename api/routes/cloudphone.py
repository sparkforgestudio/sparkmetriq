# api/routes/cloudphone.py
"""
Routes FastAPI pour le Cloud Phone Management.
CRUD formulaire pour profiles + endpoints CloudPhone + import Excel optionnel.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

from api.core.auth import get_current_user
from api.core.settings import settings
from api.core.feature_gate import require_feature
from api.services.orgs import get_entitlements
from api.schemas.users import UserResponse
from api.schemas.cloudphone import (
    ProfileCreate, ProfileUpdate, ProfileOut, ProfileListResponse, ProfileSearchParams,
    DeviceCreate, DeviceOut, DeviceListResponse, DeviceSearchParams, DeviceActionResponse,
    BulkActionRequest, BulkActionResponse, BindIn, BindResponse, UnbindIn, UnbindResponse,
    ExecIn, ExecOut, SlotCreate, SlotOut, SlotListResponse, SlotSearchParams,
    ExcelImportRequest, ExcelImportResponse, ExcelTemplateResponse,
    DeviceStatus, DeviceMetrics
)
from api.services.cloudphone.repository import (
    create_profile, get_profile, update_profile, delete_profile, list_profiles,
    create_device, get_device, list_devices, update_device,
    create_slot, get_slot, list_slots, update_slot,
    bind_slot_to_account, unbind_slot, get_device_metrics, ensure_cloudphone_indexes
)
from api.services.cloudphone.manager import (
    start_device_manager, stop_device_manager, reset_device_manager,
    install_apps_manager, assign_proxy_manager, create_slot_manager,
    bind_slot_manager, unbind_slot_manager, exec_action_manager,
    bulk_action_manager, get_device_status_manager
)
from api.services.cloudphone.excel_import import (
    import_profiles_xlsx, generate_empty_template, get_template_info,
    validate_import_file, export_profiles_to_excel
)

router = APIRouter(prefix="/mobile-cloud", tags=["CloudPhone"])

# --- Garde-fou global (si module monté par erreur) ---
if not settings.feature_cloudphone_enabled:
    def _feature_off():
        from fastapi import status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CloudPhone module disabled globally"
        )


# --- Helper pour vérifier l'entitlement ---
async def check_cloudphone_entitlement(current_user: UserResponse):
    """
    Vérifie que l'organisation a accès à CloudPhone.
    
    Args:
        current_user: Utilisateur actuel
        
    Raises:
        HTTPException: 403 si CloudPhone n'est pas activé pour l'organisation
    """
    entitlements = await get_entitlements(current_user.org_id)
    require_feature(entitlements, "cloudphone")


# ---------- PROFILES (FORM FIRST) ----------

@router.post("/profiles", response_model=ProfileOut)
async def create_profile_endpoint(
    profile_data: ProfileCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Créer un profil depuis le formulaire."""
    # Vérifier l'entitlement CloudPhone
    await check_cloudphone_entitlement(current_user)
    
    # Vérifier l'unicité du nom
    from api.services.cloudphone.repository import find_profile_by_name
    existing = await find_profile_by_name(current_user.id, profile_data.name)
    if existing:
        raise HTTPException(status_code=409, detail="Profile name already exists")
    
    profile = await create_profile(current_user.id, profile_data)
    return profile

@router.get("/profiles", response_model=ProfileListResponse)
async def list_profiles_endpoint(
    search: Optional[str] = None,
    area: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    """Lister les profils avec filtres."""
    params = ProfileSearchParams(
        search=search,
        area=area,
        tag=tag,
        page=page,
        page_size=page_size
    )
    
    return await list_profiles(current_user.id, params)

@router.get("/profiles/{profile_id}", response_model=ProfileOut)
async def get_profile_endpoint(
    profile_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupérer un profil par ID."""
    profile = await get_profile(current_user.id, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.put("/profiles/{profile_id}", response_model=ProfileOut)
async def update_profile_endpoint(
    profile_id: str,
    profile_data: ProfileUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Mettre à jour un profil."""
    # Vérifier l'unicité du nom si fourni
    if profile_data.name:
        from api.services.cloudphone.repository import find_profile_by_name
        existing = await find_profile_by_name(current_user.id, profile_data.name)
        if existing and existing.id != profile_id:
            raise HTTPException(status_code=409, detail="Profile name already exists")
    
    profile = await update_profile(current_user.id, profile_id, profile_data)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.delete("/profiles/{profile_id}", response_model=dict)
async def delete_profile_endpoint(
    profile_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Supprimer un profil."""
    success = await delete_profile(current_user.id, profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"ok": True}

# ---------- EXCEL IMPORT (OPTION) ----------

@router.post("/profiles/excel/upload", response_model=ExcelImportResponse)
async def upload_excel_profiles(
    file: UploadFile = File(...),
    upsert_mode: bool = Form(True),
    current_user: UserResponse = Depends(get_current_user)
):
    """Importer des profils depuis Excel."""
    if not file.filename.endswith(('.xlsx', '.csv')):
        raise HTTPException(status_code=400, detail="File must be .xlsx or .csv")
    
    # Lire le contenu du fichier
    content = await file.read()
    file_content = content.decode('utf-8') if file.filename.endswith('.csv') else content
    
    # Encoder en base64
    import base64
    file_content_b64 = base64.b64encode(file_content).decode('utf-8')
    
    # Importer
    return await import_profiles_xlsx(file_content_b64, file.filename, current_user.id, upsert_mode)

@router.get("/profiles/excel/template", response_model=ExcelTemplateResponse)
async def download_excel_template(current_user: UserResponse = Depends(get_current_user)):
    """Télécharger le template Excel."""
    template_b64 = await generate_empty_template()
    
    return ExcelTemplateResponse(
        template_url=f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{template_b64}",
        expires_at=datetime.now().replace(hour=23, minute=59, second=59)
    )

@router.get("/profiles/excel/info", response_model=dict)
async def get_excel_template_info(current_user: UserResponse = Depends(get_current_user)):
    """Récupérer les informations sur le template Excel."""
    return get_template_info()

@router.post("/profiles/excel/validate", response_model=dict)
async def validate_excel_file(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Valider un fichier Excel avant import."""
    if not file.filename.endswith(('.xlsx', '.csv')):
        raise HTTPException(status_code=400, detail="File must be .xlsx or .csv")
    
    content = await file.read()
    file_content = content.decode('utf-8') if file.filename.endswith('.csv') else content
    
    import base64
    file_content_b64 = base64.b64encode(file_content).decode('utf-8')
    
    return await validate_import_file(file_content_b64, file.filename)

@router.get("/profiles/excel/export", response_model=dict)
async def export_profiles_excel(
    search: Optional[str] = None,
    area: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Exporter les profils vers Excel."""
    filters = {}
    if search:
        filters["search"] = search
    if area:
        filters["area"] = area
    if tag:
        filters["tag"] = tag
    
    export_b64 = await export_profiles_to_excel(current_user.id, filters)
    
    return {
        "file_content": export_b64,
        "filename": f"profiles_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }

# ---------- DEVICES ----------

@router.post("/devices", response_model=DeviceOut)
async def create_device_endpoint(
    device_data: DeviceCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Créer un device (depuis profil si fourni)."""
    profile = None
    if device_data.profile_id:
        profile = await get_profile(current_user.id, device_data.profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
    
    device = await create_device(current_user.id, device_data, profile)
    return device

@router.get("/devices", response_model=DeviceListResponse)
async def list_devices_endpoint(
    area: Optional[str] = None,
    state: Optional[str] = None,
    app: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    """Lister les devices avec filtres."""
    params = DeviceSearchParams(
        area=area,
        state=state,
        app=app,
        page=page,
        page_size=page_size
    )
    
    return await list_devices(current_user.id, params)

@router.get("/devices/{device_id}", response_model=DeviceOut)
async def get_device_endpoint(
    device_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupérer un device par ID."""
    device = await get_device(current_user.id, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.post("/devices/{device_id}/start", response_model=DeviceActionResponse)
async def start_device_endpoint(
    device_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Démarrer un device."""
    return await start_device_manager(current_user.id, device_id)

@router.post("/devices/{device_id}/stop", response_model=DeviceActionResponse)
async def stop_device_endpoint(
    device_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Arrêter un device."""
    return await stop_device_manager(current_user.id, device_id)

@router.post("/devices/{device_id}/reset", response_model=DeviceActionResponse)
async def reset_device_endpoint(
    device_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Réinitialiser un device."""
    return await reset_device_manager(current_user.id, device_id)

@router.post("/devices/{device_id}/install", response_model=DeviceActionResponse)
async def install_apps_endpoint(
    device_id: str,
    apps: List[str],
    current_user: UserResponse = Depends(get_current_user)
):
    """Installer des applications sur un device."""
    return await install_apps_manager(current_user.id, device_id, apps)

@router.post("/devices/{device_id}/proxy", response_model=DeviceActionResponse)
async def assign_proxy_endpoint(
    device_id: str,
    proxy_ip: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Assigner un proxy à un device."""
    return await assign_proxy_manager(current_user.id, device_id, proxy_ip)

@router.get("/devices/{device_id}/status", response_model=DeviceStatus)
async def get_device_status_endpoint(
    device_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupérer le statut détaillé d'un device."""
    status = await get_device_status_manager(current_user.id, device_id)
    return DeviceStatus(**status)

# ---------- BULK ACTIONS ----------

@router.post("/devices/bulk-action", response_model=BulkActionResponse)
async def bulk_action_endpoint(
    bulk_data: BulkActionRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Effectuer une action en lot sur plusieurs devices."""
    return await bulk_action_manager(
        current_user.id,
        bulk_data.device_ids,
        bulk_data.action,
        apps=bulk_data.apps
    )

# ---------- SLOTS ----------

@router.post("/devices/{device_id}/slots", response_model=SlotOut)
async def create_slot_endpoint(
    device_id: str,
    slot_data: SlotCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Créer un slot pour une app sur un device."""
    if slot_data.device_id != device_id:
        raise HTTPException(status_code=400, detail="Device ID mismatch")
    
    return await create_slot_manager(current_user.id, device_id, slot_data.app, slot_data.isolation_strategy)

@router.get("/slots", response_model=SlotListResponse)
async def list_slots_endpoint(
    device_id: Optional[str] = None,
    app: Optional[str] = None,
    state: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    """Lister les slots avec filtres."""
    params = SlotSearchParams(
        device_id=device_id,
        app=app,
        state=state,
        page=page,
        page_size=page_size
    )
    
    return await list_slots(current_user.id, params)

@router.get("/slots/{slot_id}", response_model=SlotOut)
async def get_slot_endpoint(
    slot_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupérer un slot par ID."""
    slot = await get_slot(current_user.id, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return slot

# ---------- BIND / UNBIND / EXEC ----------

@router.post("/slots/bind", response_model=BindResponse)
async def bind_slot_endpoint(
    bind_data: BindIn,
    current_user: UserResponse = Depends(get_current_user)
):
    """Lier un slot à un compte d'application."""
    return await bind_slot_manager(current_user.id, bind_data.slot_id, bind_data.app_account_id)

@router.post("/slots/unbind", response_model=UnbindResponse)
async def unbind_slot_endpoint(
    unbind_data: UnbindIn,
    current_user: UserResponse = Depends(get_current_user)
):
    """Délier un slot."""
    return await unbind_slot_manager(current_user.id, unbind_data.slot_id)

@router.post("/slots/exec", response_model=ExecOut)
async def exec_action_endpoint(
    exec_data: ExecIn,
    current_user: UserResponse = Depends(get_current_user)
):
    """Exécuter une action sur un slot."""
    return await exec_action_manager(current_user.id, exec_data.slot_id, exec_data.action, exec_data.payload)

# ---------- METRICS & STATS ----------

@router.get("/metrics", response_model=DeviceMetrics)
async def get_device_metrics_endpoint(current_user: UserResponse = Depends(get_current_user)):
    """Récupérer les métriques des devices."""
    metrics = await get_device_metrics(current_user.id)
    return DeviceMetrics(**metrics)

@router.get("/health", response_model=dict)
async def health_check_endpoint(current_user: UserResponse = Depends(get_current_user)):
    """Vérifier la santé du service CloudPhone."""
    from api.services.cloudphone.cloudphone_client import cloudphone_client
    
    health = await cloudphone_client.health_check()
    
    return {
        "status": health["status"],
        "cloudphone_service": health,
        "database": "connected",  # Simplifié
        "timestamp": datetime.now().isoformat()
    }
