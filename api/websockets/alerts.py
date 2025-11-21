# api/websockets/alerts.py
"""
Service WebSocket pour les alertes en temps réel.
"""

from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timezone
from enum import Enum
import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from api.databases.databases import db

class AlertSeverity(str, Enum):
    """Sévérité des alertes."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(str, Enum):
    """Types d'alertes."""
    # CloudPhone
    DEVICE_UNREACHABLE = "device_unreachable"
    DEVICE_START_FAILED = "device_start_failed"
    DEVICE_STOP_FAILED = "device_stop_failed"
    APP_INSTALL_FAILED = "app_install_failed"
    PROXY_ASSIGNMENT_FAILED = "proxy_assignment_failed"
    
    # OTP
    OTP_TIMEOUT = "otp_timeout"
    OTP_PROVIDER_DOWN = "otp_provider_down"
    OTP_FAILOVER = "otp_failover"
    OTP_BUDGET_EXCEEDED = "otp_budget_exceeded"
    OTP_QUOTA_EXCEEDED = "otp_quota_exceeded"
    
    # Système
    SYSTEM_ERROR = "system_error"
    DATABASE_ERROR = "database_error"
    API_ERROR = "api_error"
    
    # Conformité
    COMPLIANCE_VIOLATION = "compliance_violation"
    AUDIT_FAILURE = "audit_failure"

class AlertStatus(str, Enum):
    """Statut des alertes."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class Alert:
    """Classe représentant une alerte."""
    
    def __init__(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        org_id: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = None
        self.alert_type = alert_type
        self.severity = severity
        self.title = title
        self.message = message
        self.org_id = org_id
        self.user_id = user_id
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.metadata = metadata or {}
        self.status = AlertStatus.ACTIVE
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.acknowledged_at = None
        self.acknowledged_by = None
        self.resolved_at = None
        self.resolved_by = None

class WebSocketManager:
    """Gestionnaire des connexions WebSocket."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, org_id: str, user_id: Optional[str] = None):
        """Connecter un WebSocket."""
        await websocket.accept()
        
        if org_id not in self.active_connections:
            self.active_connections[org_id] = set()
        
        self.active_connections[org_id].add(websocket)
        self.connection_metadata[websocket] = {
            "org_id": org_id,
            "user_id": user_id,
            "connected_at": datetime.now(timezone.utc)
        }
        
        print(f"✅ WebSocket connecté pour org_id={org_id}, user_id={user_id}")
    
    def disconnect(self, websocket: WebSocket):
        """Déconnecter un WebSocket."""
        metadata = self.connection_metadata.get(websocket)
        if metadata:
            org_id = metadata["org_id"]
            if org_id in self.active_connections:
                self.active_connections[org_id].discard(websocket)
                if not self.active_connections[org_id]:
                    del self.active_connections[org_id]
            
            del self.connection_metadata[websocket]
            print(f"❌ WebSocket déconnecté pour org_id={org_id}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Envoyer un message personnel."""
        try:
            await websocket.send_text(message)
        except WebSocketDisconnect:
            self.disconnect(websocket)
    
    async def broadcast_to_org(self, message: str, org_id: str):
        """Diffuser un message à une organisation."""
        if org_id not in self.active_connections:
            return
        
        disconnected = set()
        for websocket in self.active_connections[org_id]:
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                disconnected.add(websocket)
        
        # Nettoyer les connexions fermées
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_to_user(self, message: str, org_id: str, user_id: str):
        """Diffuser un message à un utilisateur spécifique."""
        if org_id not in self.active_connections:
            return
        
        disconnected = set()
        for websocket in self.active_connections[org_id]:
            metadata = self.connection_metadata.get(websocket)
            if metadata and metadata.get("user_id") == user_id:
                try:
                    await websocket.send_text(message)
                except WebSocketDisconnect:
                    disconnected.add(websocket)
        
        # Nettoyer les connexions fermées
        for websocket in disconnected:
            self.disconnect(websocket)
    
    def get_connection_count(self, org_id: str) -> int:
        """Récupérer le nombre de connexions pour une organisation."""
        return len(self.active_connections.get(org_id, set()))
    
    def get_all_connection_counts(self) -> Dict[str, int]:
        """Récupérer le nombre de connexions pour toutes les organisations."""
        return {org_id: len(connections) for org_id, connections in self.active_connections.items()}

# Instance globale du gestionnaire WebSocket
websocket_manager = WebSocketManager()

class AlertManager:
    """Gestionnaire des alertes."""
    
    def __init__(self):
        self.alert_rules: Dict[AlertType, Dict[str, Any]] = {}
        self.suppressed_alerts: Set[str] = set()
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
    
    async def create_alert(self, alert: Alert) -> str:
        """Créer une nouvelle alerte."""
        # Vérifier les règles de rate limiting
        if self._is_rate_limited(alert):
            return None
        
        # Vérifier si l'alerte est supprimée
        if self._is_suppressed(alert):
            return None
        
        # Sauvegarder en base de données
        alert_doc = {
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "message": alert.message,
            "org_id": alert.org_id,
            "user_id": alert.user_id,
            "resource_id": alert.resource_id,
            "resource_type": alert.resource_type,
            "metadata": alert.metadata,
            "status": alert.status.value,
            "created_at": alert.created_at,
            "updated_at": alert.updated_at,
            "acknowledged_at": alert.acknowledged_at,
            "acknowledged_by": alert.acknowledged_by,
            "resolved_at": alert.resolved_at,
            "resolved_by": alert.resolved_by
        }
        
        result = await db["alerts"].insert_one(alert_doc)
        alert.id = str(result.inserted_id)
        
        # Diffuser via WebSocket
        await self._broadcast_alert(alert)
        
        # Envoyer une notification Telegram si configuré
        await self._send_telegram_notification(alert)
        
        print(f"🚨 Alerte créée: {alert.alert_type.value} - {alert.title}")
        return alert.id
    
    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Accuser réception d'une alerte."""
        result = await db["alerts"].update_one(
            {"_id": alert_id, "status": AlertStatus.ACTIVE.value},
            {
                "$set": {
                    "status": AlertStatus.ACKNOWLEDGED.value,
                    "acknowledged_at": datetime.now(timezone.utc),
                    "acknowledged_by": user_id,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count > 0:
            # Diffuser la mise à jour
            await self._broadcast_alert_update(alert_id, "acknowledged", user_id)
            print(f"✅ Alerte {alert_id} accusée réception par {user_id}")
            return True
        
        return False
    
    async def resolve_alert(self, alert_id: str, user_id: str) -> bool:
        """Résoudre une alerte."""
        result = await db["alerts"].update_one(
            {"_id": alert_id, "status": {"$in": [AlertStatus.ACTIVE.value, AlertStatus.ACKNOWLEDGED.value]}},
            {
                "$set": {
                    "status": AlertStatus.RESOLVED.value,
                    "resolved_at": datetime.now(timezone.utc),
                    "resolved_by": user_id,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count > 0:
            # Diffuser la mise à jour
            await self._broadcast_alert_update(alert_id, "resolved", user_id)
            print(f"✅ Alerte {alert_id} résolue par {user_id}")
            return True
        
        return False
    
    async def suppress_alert(self, alert_id: str, user_id: str, reason: str) -> bool:
        """Supprimer une alerte."""
        result = await db["alerts"].update_one(
            {"_id": alert_id},
            {
                "$set": {
                    "status": AlertStatus.SUPPRESSED.value,
                    "suppressed_at": datetime.now(timezone.utc),
                    "suppressed_by": user_id,
                    "suppress_reason": reason,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count > 0:
            self.suppressed_alerts.add(alert_id)
            await self._broadcast_alert_update(alert_id, "suppressed", user_id)
            print(f"✅ Alerte {alert_id} supprimée par {user_id}")
            return True
        
        return False
    
    async def get_active_alerts(self, org_id: str) -> List[Dict[str, Any]]:
        """Récupérer les alertes actives pour une organisation."""
        cursor = db["alerts"].find({
            "org_id": org_id,
            "status": {"$in": [AlertStatus.ACTIVE.value, AlertStatus.ACKNOWLEDGED.value]}
        }).sort("created_at", -1)
        
        alerts = await cursor.to_list(None)
        for alert in alerts:
            alert["id"] = str(alert["_id"])
            del alert["_id"]
        
        return alerts
    
    async def get_alert_history(self, org_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Récupérer l'historique des alertes."""
        from datetime import timedelta
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        cursor = db["alerts"].find({
            "org_id": org_id,
            "created_at": {"$gte": start_date}
        }).sort("created_at", -1)
        
        alerts = await cursor.to_list(None)
        for alert in alerts:
            alert["id"] = str(alert["_id"])
            del alert["_id"]
        
        return alerts
    
    def _is_rate_limited(self, alert: Alert) -> bool:
        """Vérifier si l'alerte est limitée par le rate limiting."""
        key = f"{alert.alert_type.value}:{alert.org_id}"
        
        if key not in self.rate_limits:
            self.rate_limits[key] = {
                "count": 0,
                "last_reset": datetime.now(timezone.utc)
            }
        
        rate_limit = self.rate_limits[key]
        now = datetime.now(timezone.utc)
        
        # Reset toutes les heures
        if (now - rate_limit["last_reset"]).total_seconds() > 3600:
            rate_limit["count"] = 0
            rate_limit["last_reset"] = now
        
        # Limite de 10 alertes par heure par type
        if rate_limit["count"] >= 10:
            return True
        
        rate_limit["count"] += 1
        return False
    
    def _is_suppressed(self, alert: Alert) -> bool:
        """Vérifier si l'alerte est supprimée."""
        # Vérifier les règles de suppression
        if alert.alert_type in [AlertType.DEVICE_UNREACHABLE, AlertType.OTP_TIMEOUT]:
            # Supprimer les alertes répétitives
            return False
        
        return False
    
    async def _broadcast_alert(self, alert: Alert):
        """Diffuser une alerte via WebSocket."""
        message = {
            "type": "alert",
            "action": "created",
            "data": {
                "id": alert.id,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "org_id": alert.org_id,
                "user_id": alert.user_id,
                "resource_id": alert.resource_id,
                "resource_type": alert.resource_type,
                "metadata": alert.metadata,
                "status": alert.status.value,
                "created_at": alert.created_at.isoformat(),
                "updated_at": alert.updated_at.isoformat()
            }
        }
        
        await websocket_manager.broadcast_to_org(json.dumps(message), alert.org_id)
    
    async def _broadcast_alert_update(self, alert_id: str, action: str, user_id: str):
        """Diffuser une mise à jour d'alerte."""
        message = {
            "type": "alert",
            "action": action,
            "data": {
                "id": alert_id,
                "user_id": user_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Récupérer l'org_id de l'alerte
        alert_doc = await db["alerts"].find_one({"_id": alert_id})
        if alert_doc:
            await websocket_manager.broadcast_to_org(json.dumps(message), alert_doc["org_id"])
    
    async def _send_telegram_notification(self, alert: Alert):
        """Envoyer une notification Telegram."""
        # Pour V1, on simule l'envoi
        if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
            print(f"📱 Notification Telegram: {alert.title} - {alert.message}")
    
    async def setup_alert_rules(self):
        """Configurer les règles d'alerte."""
        self.alert_rules = {
            AlertType.DEVICE_UNREACHABLE: {
                "severity": AlertSeverity.ERROR,
                "rate_limit": 5,  # 5 par heure
                "suppress_after": 3  # Supprimer après 3 occurrences
            },
            AlertType.OTP_TIMEOUT: {
                "severity": AlertSeverity.WARNING,
                "rate_limit": 10,
                "suppress_after": 5
            },
            AlertType.OTP_PROVIDER_DOWN: {
                "severity": AlertSeverity.CRITICAL,
                "rate_limit": 1,
                "suppress_after": 0
            },
            AlertType.OTP_BUDGET_EXCEEDED: {
                "severity": AlertSeverity.ERROR,
                "rate_limit": 1,
                "suppress_after": 0
            }
        }
    
    async def ensure_alert_indexes(self):
        """Créer les index pour les alertes."""
        await db["alerts"].create_index([("org_id", 1), ("created_at", -1)])
        await db["alerts"].create_index([("org_id", 1), ("status", 1)])
        await db["alerts"].create_index([("org_id", 1), ("alert_type", 1)])
        await db["alerts"].create_index([("org_id", 1), ("severity", 1)])
        await db["alerts"].create_index([("org_id", 1), ("resource_type", 1), ("resource_id", 1)])

# Instance globale du gestionnaire d'alertes
alert_manager = AlertManager()

# ---------- FONCTIONS UTILITAIRES POUR LES ALERTES ----------

async def create_cloudphone_alert(
    alert_type: AlertType,
    title: str,
    message: str,
    org_id: str,
    user_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Créer une alerte CloudPhone."""
    severity_map = {
        AlertType.DEVICE_UNREACHABLE: AlertSeverity.ERROR,
        AlertType.DEVICE_START_FAILED: AlertSeverity.ERROR,
        AlertType.DEVICE_STOP_FAILED: AlertSeverity.WARNING,
        AlertType.APP_INSTALL_FAILED: AlertSeverity.WARNING,
        AlertType.PROXY_ASSIGNMENT_FAILED: AlertSeverity.WARNING
    }
    
    alert = Alert(
        alert_type=alert_type,
        severity=severity_map.get(alert_type, AlertSeverity.WARNING),
        title=title,
        message=message,
        org_id=org_id,
        user_id=user_id,
        resource_id=resource_id,
        resource_type=resource_type,
        metadata=metadata
    )
    
    return await alert_manager.create_alert(alert)

async def create_otp_alert(
    alert_type: AlertType,
    title: str,
    message: str,
    org_id: str,
    user_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Créer une alerte OTP."""
    severity_map = {
        AlertType.OTP_TIMEOUT: AlertSeverity.WARNING,
        AlertType.OTP_PROVIDER_DOWN: AlertSeverity.CRITICAL,
        AlertType.OTP_FAILOVER: AlertSeverity.INFO,
        AlertType.OTP_BUDGET_EXCEEDED: AlertSeverity.ERROR,
        AlertType.OTP_QUOTA_EXCEEDED: AlertSeverity.ERROR
    }
    
    alert = Alert(
        alert_type=alert_type,
        severity=severity_map.get(alert_type, AlertSeverity.WARNING),
        title=title,
        message=message,
        org_id=org_id,
        user_id=user_id,
        resource_id=resource_id,
        resource_type=resource_type,
        metadata=metadata
    )
    
    return await alert_manager.create_alert(alert)

async def create_system_alert(
    alert_type: AlertType,
    title: str,
    message: str,
    org_id: str,
    user_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Créer une alerte système."""
    severity_map = {
        AlertType.SYSTEM_ERROR: AlertSeverity.ERROR,
        AlertType.DATABASE_ERROR: AlertSeverity.CRITICAL,
        AlertType.API_ERROR: AlertSeverity.ERROR
    }
    
    alert = Alert(
        alert_type=alert_type,
        severity=severity_map.get(alert_type, AlertSeverity.ERROR),
        title=title,
        message=message,
        org_id=org_id,
        user_id=user_id,
        resource_id=resource_id,
        resource_type=resource_type,
        metadata=metadata
    )
    
    return await alert_manager.create_alert(alert)

# ---------- INITIALISATION ----------

async def initialize_websockets():
    """Initialiser le système WebSocket."""
    await alert_manager.setup_alert_rules()
    await alert_manager.ensure_alert_indexes()
    print("✅ Système WebSocket et alertes initialisé")



