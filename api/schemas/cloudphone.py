# api/schemas/cloudphone.py
"""
Schémas Pydantic pour le Cloud Phone Management.
Approche form-first avec import Excel optionnel.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# ---------- Profiles (FORM FIRST) ----------
class ProfileBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    area: Optional[str] = Field(None, description="Zone géographique interne (ex: EU, US, ASIA)")
    lang: Optional[str] = Field(None, description="Langue par défaut du device (ex: fr-FR)")
    proxy_template: Optional[str] = Field(None, description="Ex. residential_fixed_eu_01")
    tags: List[str] = Field(default_factory=list)
    remark: Optional[str] = None
    provider_ref: Optional[str] = Field(None, description="Identifiant externe éventuel (depuis Excel)")

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    area: Optional[str] = None
    lang: Optional[str] = None
    proxy_template: Optional[str] = None
    tags: Optional[List[str]] = None
    remark: Optional[str] = None
    provider_ref: Optional[str] = None

class ProfileOut(ProfileBase):
    id: str
    org_id: str
    created_at: datetime
    updated_at: datetime

class ProfileListResponse(BaseModel):
    items: List[ProfileOut]
    total: int
    page: int
    page_size: int

# ---------- Devices ----------
class DeviceCreate(BaseModel):
    profile_id: Optional[str] = Field(None, description="Créer depuis ce template si fourni")

class DeviceOut(BaseModel):
    id: str
    org_id: str
    provider_ref: Optional[str] = None
    state: Literal["running", "stopped", "error", "banned"]
    area: Optional[str] = None
    lang: Optional[str] = None
    proxy_current: Optional[str] = None
    fingerprint: Optional[str] = None
    slots_count: int
    created_at: datetime
    updated_at: datetime

class DeviceListResponse(BaseModel):
    items: List[DeviceOut]
    total: int
    page: int
    page_size: int

class DeviceActionResponse(BaseModel):
    ok: bool
    action: str
    device_id: str
    new_state: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class BulkActionRequest(BaseModel):
    device_ids: List[str]
    action: Literal["start", "stop", "reset", "install"]
    apps: Optional[List[str]] = None

class BulkActionResponse(BaseModel):
    ok: bool
    action: str
    results: List[Dict[str, Any]]
    success_count: int
    failed_count: int

# ---------- App Accounts ----------
class AppAccountIn(BaseModel):
    app: Literal["instagram", "telegram", "tiktok", "twitter", "reddit", "onlyfans"]
    username: str
    status: Optional[str] = None
    risk_level: Optional[str] = None
    last_login_at: Optional[datetime] = None

class AppAccountOut(AppAccountIn):
    id: str
    org_id: str
    created_at: datetime
    updated_at: datetime

class AppAccountListResponse(BaseModel):
    items: List[AppAccountOut]
    total: int

# ---------- Slots ----------
class SlotCreate(BaseModel):
    device_id: str
    app: Literal["instagram", "telegram", "tiktok", "twitter", "reddit", "onlyfans"]
    isolation_strategy: Literal["android_user", "work_profile", "cloned_app", "container"]
    proxy_override: Optional[str] = None

class SlotOut(BaseModel):
    id: str
    device_id: str
    app: str
    slot_index: int
    isolation_strategy: str
    proxy_override: Optional[str] = None
    state: Literal["vacant", "bound", "error"]
    bound_app_account_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class SlotListResponse(BaseModel):
    items: List[SlotOut]
    total: int

# ---------- Bind / Unbind / Exec ----------
class BindIn(BaseModel):
    slot_id: str
    app_account_id: str

class UnbindIn(BaseModel):
    slot_id: str

class ExecIn(BaseModel):
    slot_id: str
    action: Literal["open_app", "switch_account", "tap", "input", "intent", "post_story", "post_media"]
    payload: Dict[str, Any] = Field(default_factory=dict)

class ExecOut(BaseModel):
    ok: bool
    action: str
    payload: Dict[str, Any]
    details: Optional[Dict[str, Any]] = None

class BindResponse(BaseModel):
    ok: bool
    slot_id: str
    app_account_id: str
    details: Optional[Dict[str, Any]] = None

class UnbindResponse(BaseModel):
    ok: bool
    slot_id: str
    details: Optional[Dict[str, Any]] = None

# ---------- Excel Import (OPTION) ----------
class ExcelImportRequest(BaseModel):
    file_content: str  # Base64 encoded
    file_name: str
    upsert_mode: bool = True

class ExcelImportResponse(BaseModel):
    ok: bool
    imported_count: int
    updated_count: int
    errors: List[Dict[str, Any]]
    summary: Dict[str, Any]

class ExcelTemplateResponse(BaseModel):
    template_url: str
    expires_at: datetime

# ---------- Device Status & Monitoring ----------
class DeviceStatus(BaseModel):
    device_id: str
    state: str
    proxy_active: Optional[str] = None
    apps_installed: List[str] = []
    last_logs: List[Dict[str, Any]] = []
    uptime: Optional[int] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None

class DeviceMetrics(BaseModel):
    total_devices: int
    running_devices: int
    stopped_devices: int
    error_devices: int
    banned_devices: int
    total_slots: int
    bound_slots: int
    vacant_slots: int

# ---------- Search & Filters ----------
class ProfileSearchParams(BaseModel):
    search: Optional[str] = None
    area: Optional[str] = None
    tag: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)

class DeviceSearchParams(BaseModel):
    area: Optional[str] = None
    state: Optional[str] = None
    app: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)

class SlotSearchParams(BaseModel):
    device_id: Optional[str] = None
    app: Optional[str] = None
    state: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)




