# api/services/cloudphone/manager.py
"""
Manager CloudPhone - Orchestration des opérations devices/slots/bind/exec.
Interface principale pour les opérations CloudPhone.
"""

from typing import Dict, Any, List, Optional
from api.services.cloudphone.repository import (
    get_device, update_device, bind_slot_to_account, unbind_slot,
    get_slot, update_slot
)
from api.services.cloudphone.cloudphone_client import (
    start_device, stop_device, reset_device, install_apps, 
    assign_proxy, execute_action, bulk_action
)
from api.services.cloudphone.selection import ensure_slot
from api.schemas.cloudphone import (
    DeviceOut, SlotOut, DeviceActionResponse, BulkActionResponse,
    BindResponse, UnbindResponse, ExecOut
)

async def start_device_manager(org_id: str, device_id: str) -> DeviceActionResponse:
    """Démarrer un device."""
    device = await get_device(org_id, device_id)
    if not device:
        return DeviceActionResponse(
            ok=False,
            action="start",
            device_id=device_id,
            details={"error": "Device not found"}
        )
    
    if device.state == "running":
        return DeviceActionResponse(
            ok=True,
            action="start",
            device_id=device_id,
            new_state="running",
            details={"message": "Device already running"}
        )
    
    try:
        if not device.provider_ref:
            return DeviceActionResponse(
                ok=False,
                action="start",
                device_id=device_id,
                details={"error": "No provider reference"}
            )
        
        result = await start_device(device.provider_ref)
        
        if result.get("status") == "running":
            await update_device(org_id, device_id, {"state": "running"})
            return DeviceActionResponse(
                ok=True,
                action="start",
                device_id=device_id,
                new_state="running",
                details=result
            )
        else:
            await update_device(org_id, device_id, {"state": "error"})
            return DeviceActionResponse(
                ok=False,
                action="start",
                device_id=device_id,
                new_state="error",
                details=result
            )
            
    except Exception as e:
        await update_device(org_id, device_id, {"state": "error"})
        return DeviceActionResponse(
            ok=False,
            action="start",
            device_id=device_id,
            new_state="error",
            details={"error": str(e)}
        )

async def stop_device_manager(org_id: str, device_id: str) -> DeviceActionResponse:
    """Arrêter un device."""
    device = await get_device(org_id, device_id)
    if not device:
        return DeviceActionResponse(
            ok=False,
            action="stop",
            device_id=device_id,
            details={"error": "Device not found"}
        )
    
    if device.state == "stopped":
        return DeviceActionResponse(
            ok=True,
            action="stop",
            device_id=device_id,
            new_state="stopped",
            details={"message": "Device already stopped"}
        )
    
    try:
        if not device.provider_ref:
            return DeviceActionResponse(
                ok=False,
                action="stop",
                device_id=device_id,
                details={"error": "No provider reference"}
            )
        
        result = await stop_device(device.provider_ref)
        
        if result.get("status") == "stopped":
            await update_device(org_id, device_id, {"state": "stopped"})
            return DeviceActionResponse(
                ok=True,
                action="stop",
                device_id=device_id,
                new_state="stopped",
                details=result
            )
        else:
            return DeviceActionResponse(
                ok=False,
                action="stop",
                device_id=device_id,
                details=result
            )
            
    except Exception as e:
        return DeviceActionResponse(
            ok=False,
            action="stop",
            device_id=device_id,
            details={"error": str(e)}
        )

async def reset_device_manager(org_id: str, device_id: str) -> DeviceActionResponse:
    """Réinitialiser un device."""
    device = await get_device(org_id, device_id)
    if not device:
        return DeviceActionResponse(
            ok=False,
            action="reset",
            device_id=device_id,
            details={"error": "Device not found"}
        )
    
    try:
        if not device.provider_ref:
            return DeviceActionResponse(
                ok=False,
                action="reset",
                device_id=device_id,
                details={"error": "No provider reference"}
            )
        
        result = await reset_device(device.provider_ref)
        
        if result.get("status") == "reset":
            await update_device(org_id, device_id, {"state": "stopped"})
            return DeviceActionResponse(
                ok=True,
                action="reset",
                device_id=device_id,
                new_state="stopped",
                details=result
            )
        else:
            return DeviceActionResponse(
                ok=False,
                action="reset",
                device_id=device_id,
                details=result
            )
            
    except Exception as e:
        return DeviceActionResponse(
            ok=False,
            action="reset",
            device_id=device_id,
            details={"error": str(e)}
        )

async def install_apps_manager(org_id: str, device_id: str, apps: List[str]) -> DeviceActionResponse:
    """Installer des applications sur un device."""
    device = await get_device(org_id, device_id)
    if not device:
        return DeviceActionResponse(
            ok=False,
            action="install",
            device_id=device_id,
            details={"error": "Device not found"}
        )
    
    try:
        if not device.provider_ref:
            return DeviceActionResponse(
                ok=False,
                action="install",
                device_id=device_id,
                details={"error": "No provider reference"}
            )
        
        result = await install_apps(device.provider_ref, apps)
        
        if result.get("status") == "installed":
            return DeviceActionResponse(
                ok=True,
                action="install",
                device_id=device_id,
                details=result
            )
        else:
            return DeviceActionResponse(
                ok=False,
                action="install",
                device_id=device_id,
                details=result
            )
            
    except Exception as e:
        return DeviceActionResponse(
            ok=False,
            action="install",
            device_id=device_id,
            details={"error": str(e)}
        )

async def assign_proxy_manager(org_id: str, device_id: str, proxy_ip: str) -> DeviceActionResponse:
    """Assigner un proxy à un device."""
    device = await get_device(org_id, device_id)
    if not device:
        return DeviceActionResponse(
            ok=False,
            action="assign_proxy",
            device_id=device_id,
            details={"error": "Device not found"}
        )
    
    try:
        if not device.provider_ref:
            return DeviceActionResponse(
                ok=False,
                action="assign_proxy",
                device_id=device_id,
                details={"error": "No provider reference"}
            )
        
        result = await assign_proxy(device.provider_ref, proxy_ip)
        
        if result.get("status") == "assigned":
            await update_device(org_id, device_id, {"proxy_current": proxy_ip})
            return DeviceActionResponse(
                ok=True,
                action="assign_proxy",
                device_id=device_id,
                details=result
            )
        else:
            return DeviceActionResponse(
                ok=False,
                action="assign_proxy",
                device_id=device_id,
                details=result
            )
            
    except Exception as e:
        return DeviceActionResponse(
            ok=False,
            action="assign_proxy",
            device_id=device_id,
            details={"error": str(e)}
        )

async def create_slot_manager(org_id: str, device_id: str, app: str, isolation_strategy: str = "android_user") -> SlotOut:
    """Créer un slot pour une app sur un device."""
    device = await get_device(org_id, device_id)
    if not device:
        raise ValueError("Device not found")
    
    return await ensure_slot(org_id, device, app)

async def bind_slot_manager(org_id: str, slot_id: str, app_account_id: str) -> BindResponse:
    """Lier un slot à un compte d'application."""
    slot = await get_slot(org_id, slot_id)
    if not slot:
        return BindResponse(
            ok=False,
            slot_id=slot_id,
            app_account_id=app_account_id,
            details={"error": "Slot not found"}
        )
    
    if slot.state != "vacant":
        return BindResponse(
            ok=False,
            slot_id=slot_id,
            app_account_id=app_account_id,
            details={"error": f"Slot is not vacant (current state: {slot.state})"}
        )
    
    success = await bind_slot_to_account(org_id, slot_id, app_account_id)
    
    if success:
        return BindResponse(
            ok=True,
            slot_id=slot_id,
            app_account_id=app_account_id,
            details={"message": "Slot bound successfully"}
        )
    else:
        return BindResponse(
            ok=False,
            slot_id=slot_id,
            app_account_id=app_account_id,
            details={"error": "Failed to bind slot"}
        )

async def unbind_slot_manager(org_id: str, slot_id: str) -> UnbindResponse:
    """Délier un slot."""
    slot = await get_slot(org_id, slot_id)
    if not slot:
        return UnbindResponse(
            ok=False,
            slot_id=slot_id,
            details={"error": "Slot not found"}
        )
    
    if slot.state != "bound":
        return UnbindResponse(
            ok=False,
            slot_id=slot_id,
            details={"error": f"Slot is not bound (current state: {slot.state})"}
        )
    
    success = await unbind_slot(org_id, slot_id)
    
    if success:
        return UnbindResponse(
            ok=True,
            slot_id=slot_id,
            details={"message": "Slot unbound successfully"}
        )
    else:
        return UnbindResponse(
            ok=False,
            slot_id=slot_id,
            details={"error": "Failed to unbind slot"}
        )

async def exec_action_manager(org_id: str, slot_id: str, action: str, payload: Dict[str, Any]) -> ExecOut:
    """Exécuter une action sur un slot."""
    slot = await get_slot(org_id, slot_id)
    if not slot:
        return ExecOut(
            ok=False,
            action=action,
            payload=payload,
            details={"error": "Slot not found"}
        )
    
    if slot.state != "bound":
        return ExecOut(
            ok=False,
            action=action,
            payload=payload,
            details={"error": f"Slot is not bound (current state: {slot.state})"}
        )
    
    # Récupérer le device pour obtenir le provider_ref
    device = await get_device(org_id, slot.device_id)
    if not device or not device.provider_ref:
        return ExecOut(
            ok=False,
            action=action,
            payload=payload,
            details={"error": "Device not found or no provider reference"}
        )
    
    try:
        result = await execute_action(device.provider_ref, slot.slot_index, action, payload)
        
        return ExecOut(
            ok=result.get("ok", False),
            action=action,
            payload=payload,
            details=result
        )
        
    except Exception as e:
        return ExecOut(
            ok=False,
            action=action,
            payload=payload,
            details={"error": str(e)}
        )

async def bulk_action_manager(org_id: str, device_ids: List[str], action: str, **kwargs) -> BulkActionResponse:
    """Effectuer une action en lot sur plusieurs devices."""
    results = []
    success_count = 0
    failed_count = 0
    
    # Récupérer les provider_refs des devices
    device_refs = []
    for device_id in device_ids:
        device = await get_device(org_id, device_id)
        if device and device.provider_ref:
            device_refs.append(device.provider_ref)
        else:
            results.append({
                "device_id": device_id,
                "success": False,
                "error": "Device not found or no provider reference"
            })
            failed_count += 1
    
    if device_refs:
        try:
            # Effectuer l'action en lot via le client CloudPhone
            bulk_result = await bulk_action(device_refs, action, **kwargs)
            
            # Traiter les résultats
            for i, device_ref in enumerate(device_refs):
                device_id = device_ids[i]
                result = bulk_result.get("results", [{}])[i] if i < len(bulk_result.get("results", [])) else {}
                
                if result.get("success", False):
                    success_count += 1
                    results.append({
                        "device_id": device_id,
                        "success": True,
                        "details": result
                    })
                    
                    # Mettre à jour l'état du device si nécessaire
                    if action in ["start", "stop", "reset"]:
                        new_state = "running" if action == "start" else "stopped"
                        await update_device(org_id, device_id, {"state": new_state})
                else:
                    failed_count += 1
                    results.append({
                        "device_id": device_id,
                        "success": False,
                        "error": result.get("error", "Unknown error")
                    })
                    
        except Exception as e:
            # En cas d'erreur globale, marquer tous les devices comme échoués
            for device_id in device_ids:
                if not any(r.get("device_id") == device_id for r in results):
                    results.append({
                        "device_id": device_id,
                        "success": False,
                        "error": str(e)
                    })
                    failed_count += 1
    
    return BulkActionResponse(
        ok=success_count > 0,
        action=action,
        results=results,
        success_count=success_count,
        failed_count=failed_count
    )

async def get_device_status_manager(org_id: str, device_id: str) -> Dict[str, Any]:
    """Récupérer le statut détaillé d'un device."""
    device = await get_device(org_id, device_id)
    if not device:
        return {"error": "Device not found"}
    
    if not device.provider_ref:
        return {
            "device_id": device_id,
            "state": device.state,
            "error": "No provider reference"
        }
    
    try:
        from api.services.cloudphone.cloudphone_client import get_device_status
        status = await get_device_status(device.provider_ref)
        
        return {
            "device_id": device_id,
            "state": device.state,
            "provider_ref": device.provider_ref,
            "area": device.area,
            "lang": device.lang,
            "proxy_current": device.proxy_current,
            "fingerprint": device.fingerprint,
            "slots_count": device.slots_count,
            **status
        }
        
    except Exception as e:
        return {
            "device_id": device_id,
            "state": device.state,
            "error": str(e)
        }




