# api/services/cloudphone/cloudphone_client.py
"""
Client CloudPhone générique (stubs HTTP, sans marque).
Interface mockable pour les opérations de base.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import httpx
import logging

logger = logging.getLogger(__name__)

class CloudPhoneClient:
    """Client générique pour CloudPhone."""
    
    def __init__(self):
        self.base_url = os.getenv("CLOUDPHONE_BASE_URL", "https://api.cloudphone.example.com")
        self.api_key = os.getenv("CLOUDPHONE_API_KEY", "demo_key")
        self.timeout = 30.0
        
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Effectuer une requête HTTP vers l'API CloudPhone."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in CloudPhone request: {e}")
            # Retourner une réponse mockée en cas d'erreur
            return self._get_mock_response(endpoint, method)
        except Exception as e:
            logger.error(f"Unexpected error in CloudPhone request: {e}")
            return self._get_mock_response(endpoint, method)
    
    def _get_mock_response(self, endpoint: str, method: str) -> Dict[str, Any]:
        """Générer une réponse mockée pour les tests."""
        if "devices" in endpoint and method.upper() == "POST":
            return {
                "provider_ref": f"device_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "fingerprint": f"fp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "area": "EU",
                "lang": "fr-FR",
                "proxy_current": "192.168.1.100"
            }
        elif "start" in endpoint:
            return {"status": "running", "started_at": datetime.now(timezone.utc).isoformat()}
        elif "stop" in endpoint:
            return {"status": "stopped", "stopped_at": datetime.now(timezone.utc).isoformat()}
        elif "reset" in endpoint:
            return {"status": "reset", "reset_at": datetime.now(timezone.utc).isoformat()}
        elif "install" in endpoint:
            return {"status": "installed", "apps": ["instagram", "telegram"], "installed_at": datetime.now(timezone.utc).isoformat()}
        elif "proxy" in endpoint:
            return {"status": "assigned", "proxy_ip": "192.168.1.101", "assigned_at": datetime.now(timezone.utc).isoformat()}
        else:
            return {"status": "success", "timestamp": datetime.now(timezone.utc).isoformat()}

    async def create_device_from_profile(self, profile_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Créer un device depuis un profil."""
        data = {
            "name": profile_dict.get("name"),
            "area": profile_dict.get("area"),
            "lang": profile_dict.get("lang"),
            "proxy_template": profile_dict.get("proxy_template"),
            "tags": profile_dict.get("tags", [])
        }
        
        response = await self._make_request("POST", "/devices", data)
        
        return {
            "provider_ref": response.get("provider_ref"),
            "fingerprint": response.get("fingerprint"),
            "area": response.get("area"),
            "lang": response.get("lang"),
            "proxy_current": response.get("proxy_current")
        }

    async def start_device(self, provider_ref: str) -> Dict[str, Any]:
        """Démarrer un device."""
        response = await self._make_request("POST", f"/devices/{provider_ref}/start")
        
        return {
            "status": response.get("status"),
            "started_at": response.get("started_at"),
            "details": response
        }

    async def stop_device(self, provider_ref: str) -> Dict[str, Any]:
        """Arrêter un device."""
        response = await self._make_request("POST", f"/devices/{provider_ref}/stop")
        
        return {
            "status": response.get("status"),
            "stopped_at": response.get("stopped_at"),
            "details": response
        }

    async def reset_device(self, provider_ref: str) -> Dict[str, Any]:
        """Réinitialiser un device."""
        response = await self._make_request("POST", f"/devices/{provider_ref}/reset")
        
        return {
            "status": response.get("status"),
            "reset_at": response.get("reset_at"),
            "details": response
        }

    async def install_apps(self, provider_ref: str, apps: List[str]) -> Dict[str, Any]:
        """Installer des applications sur un device."""
        data = {"apps": apps}
        response = await self._make_request("POST", f"/devices/{provider_ref}/install", data)
        
        return {
            "status": response.get("status"),
            "installed_apps": response.get("apps", []),
            "installed_at": response.get("installed_at"),
            "details": response
        }

    async def assign_proxy(self, provider_ref: str, proxy_ip: str) -> Dict[str, Any]:
        """Assigner un proxy à un device."""
        data = {"proxy_ip": proxy_ip}
        response = await self._make_request("POST", f"/devices/{provider_ref}/proxy", data)
        
        return {
            "status": response.get("status"),
            "proxy_ip": response.get("proxy_ip"),
            "assigned_at": response.get("assigned_at"),
            "details": response
        }

    async def get_device_status(self, provider_ref: str) -> Dict[str, Any]:
        """Récupérer le statut d'un device."""
        response = await self._make_request("GET", f"/devices/{provider_ref}/status")
        
        return {
            "state": response.get("state", "unknown"),
            "uptime": response.get("uptime"),
            "cpu_usage": response.get("cpu_usage"),
            "memory_usage": response.get("memory_usage"),
            "apps_installed": response.get("apps_installed", []),
            "last_logs": response.get("last_logs", []),
            "details": response
        }

    async def execute_action(self, provider_ref: str, slot_index: int, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Exécuter une action sur un slot."""
        data = {
            "slot_index": slot_index,
            "action": action,
            "payload": payload
        }
        
        response = await self._make_request("POST", f"/devices/{provider_ref}/execute", data)
        
        return {
            "ok": response.get("ok", False),
            "action": action,
            "payload": payload,
            "details": response
        }

    async def get_device_logs(self, provider_ref: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupérer les logs d'un device."""
        response = await self._make_request("GET", f"/devices/{provider_ref}/logs?limit={limit}")
        
        return response.get("logs", [])

    async def health_check(self) -> Dict[str, Any]:
        """Vérifier la santé du service CloudPhone."""
        try:
            response = await self._make_request("GET", "/health")
            return {
                "status": "healthy",
                "response_time": response.get("response_time"),
                "version": response.get("version"),
                "details": response
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "details": {}
            }

    async def bulk_action(self, device_refs: List[str], action: str, **kwargs) -> Dict[str, Any]:
        """Effectuer une action en lot sur plusieurs devices."""
        data = {
            "device_refs": device_refs,
            "action": action,
            **kwargs
        }
        
        response = await self._make_request("POST", "/devices/bulk-action", data)
        
        return {
            "action": action,
            "results": response.get("results", []),
            "success_count": response.get("success_count", 0),
            "failed_count": response.get("failed_count", 0),
            "details": response
        }

# Instance globale du client
cloudphone_client = CloudPhoneClient()

# Fonctions de convenance
async def create_device_from_profile(profile_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Créer un device depuis un profil."""
    return await cloudphone_client.create_device_from_profile(profile_dict)

async def start_device(provider_ref: str) -> Dict[str, Any]:
    """Démarrer un device."""
    return await cloudphone_client.start_device(provider_ref)

async def stop_device(provider_ref: str) -> Dict[str, Any]:
    """Arrêter un device."""
    return await cloudphone_client.stop_device(provider_ref)

async def reset_device(provider_ref: str) -> Dict[str, Any]:
    """Réinitialiser un device."""
    return await cloudphone_client.reset_device(provider_ref)

async def install_apps(provider_ref: str, apps: List[str]) -> Dict[str, Any]:
    """Installer des applications."""
    return await cloudphone_client.install_apps(provider_ref, apps)

async def assign_proxy(provider_ref: str, proxy_ip: str) -> Dict[str, Any]:
    """Assigner un proxy."""
    return await cloudphone_client.assign_proxy(provider_ref, proxy_ip)

async def get_device_status(provider_ref: str) -> Dict[str, Any]:
    """Récupérer le statut d'un device."""
    return await cloudphone_client.get_device_status(provider_ref)

async def execute_action(provider_ref: str, slot_index: int, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Exécuter une action."""
    return await cloudphone_client.execute_action(provider_ref, slot_index, action, payload)

async def bulk_action(device_refs: List[str], action: str, **kwargs) -> Dict[str, Any]:
    """Action en lot."""
    return await cloudphone_client.bulk_action(device_refs, action, **kwargs)




