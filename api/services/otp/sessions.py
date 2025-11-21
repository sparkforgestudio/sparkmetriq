# api/services/otp/sessions.py
"""
Gestion des sessions OTP avec FSM et intégration slot/device.
États: INIT → RESERVED → WAITING_CODE → DELIVERED_TO_ADMIN → APPLIED_SUCCESS|APPLIED_FAILED
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from api.databases.databases import get_core_db

# Utiliser la base Core pour OTP
db = get_core_db()
from api.services.otp.providers.registry import get_primary_adapter
from api.services.otp.parsers import extract_code, mask_code, extract_message_preview
from api.services.otp.policy import enforce_geo, validate_session_constraints
from api.services.cloudphone.repository import get_slot, get_device
from api.schemas.otp import OTPReserveIn, OTPPollOut, OTPAcknowledgeIn, OTPApplyIn, OTPState

class OTPSessionManager:
    """Gestionnaire des sessions OTP."""
    
    def __init__(self):
        self.adapter = get_primary_adapter()
        self.timeout_minutes = 10  # Timeout par défaut
    
    async def reserve(self, payload: OTPReserveIn, org_id: str) -> OTPPollOut:
        """
        Réserver un numéro OTP pour une session.
        
        Args:
            payload: Données de réservation
            org_id: ID de l'organisation
            
        Returns:
            OTPPollOut avec état RESERVED
        """
        # Valider les contraintes
        is_valid, reason = validate_session_constraints(payload.constraints)
        if not is_valid:
            raise ValueError(f"Invalid constraints: {reason}")
        
        # Charger le slot et le device
        slot = await get_slot(org_id, payload.slot_id)
        if not slot:
            raise ValueError("Slot not found")
        
        device = await get_device(org_id, slot.device_id)
        if not device:
            raise ValueError("Device not found")
        
        # Enforcer la politique géo
        geo_valid, geo_reason = enforce_geo(payload.country, device.__dict__, payload.constraints)
        if not geo_valid:
            raise ValueError(f"Geo policy violation: {geo_reason}")
        
        # Réserver le numéro via l'adapter
        try:
            adapter_result = await self.adapter.reserve_number(
                app=payload.app,
                country=payload.country,
                timeout=self.timeout_minutes * 60,
                **payload.constraints
            )
        except Exception as e:
            raise ValueError(f"Failed to reserve number: {str(e)}")
        
        # Créer la session en base
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self.timeout_minutes)
        
        session_doc = {
            "org_id": org_id,
            "app": payload.app,
            "country": payload.country,
            "slot_id": payload.slot_id,
            "device_id": slot.device_id,
            "state": "RESERVED",
            "provider": self.adapter.name,
            "provider_session_id": adapter_result["provider_session_id"],
            "number": adapter_result["number"],
            "code_masked": None,
            "message_preview": None,
            "constraints": payload.constraints,
            "metadata": payload.metadata or {},
            "created_at": now,
            "updated_at": now,
            "expires_at": expires_at,
            "applied_at": None
        }
        
        result = await db["otp_sessions"].insert_one(session_doc)
        session_id = str(result.inserted_id)
        
        return OTPPollOut(
            session_id=session_id,
            state="RESERVED",
            code_masked=None,
            message_preview=None,
            provider=self.adapter.name,
            number=adapter_result["number"],
            updated_at=now,
            expires_at=expires_at
        )
    
    async def poll(self, session_id: str, org_id: str) -> OTPPollOut:
        """
        Poller une session OTP pour récupérer le code.
        
        Args:
            session_id: ID de la session
            org_id: ID de l'organisation
            
        Returns:
            OTPPollOut avec l'état actuel
        """
        # Récupérer la session
        session = await db["otp_sessions"].find_one({
            "_id": ObjectId(session_id),
            "org_id": org_id
        })
        
        if not session:
            raise ValueError("Session not found")
        
        # Si état final, retourner tel quel
        if session["state"] in ["APPLIED_SUCCESS", "APPLIED_FAILED", "CANCELLED", "FAILED", "BANNED"]:
            return self._session_to_poll_out(session)
        
        # Vérifier l'expiration
        if session["expires_at"] < datetime.now(timezone.utc):
            await self._update_session_state(session_id, "FAILED", {"reason": "expired"})
            session["state"] = "FAILED"
            return self._session_to_poll_out(session)
        
        # Si pas encore en attente, passer à WAITING_CODE
        if session["state"] == "RESERVED":
            await self._update_session_state(session_id, "WAITING_CODE")
            session["state"] = "WAITING_CODE"
        
        # Essayer de récupérer le SMS
        try:
            sms_text = await self.adapter.get_sms(session["provider_session_id"])
            
            if sms_text:
                # Extraire le code
                code = extract_code(session["app"], sms_text)
                
                if code:
                    # Masquer le code et créer l'aperçu
                    code_masked = mask_code(code)
                    message_preview = extract_message_preview(sms_text)
                    
                    # Mettre à jour la session
                    await db["otp_sessions"].update_one(
                        {"_id": ObjectId(session_id)},
                        {
                            "$set": {
                                "state": "DELIVERED_TO_ADMIN",
                                "code_masked": code_masked,
                                "message_preview": message_preview,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
                    
                    # Broadcast WebSocket
                    await self._broadcast_otp_received(session_id, code_masked, message_preview)
                    
                    # Mettre à jour l'objet session
                    session["state"] = "DELIVERED_TO_ADMIN"
                    session["code_masked"] = code_masked
                    session["message_preview"] = message_preview
                else:
                    # SMS reçu mais pas de code valide
                    await self._update_session_state(session_id, "FAILED", {"reason": "no_code_found"})
                    session["state"] = "FAILED"
            
        except Exception as e:
            # Erreur lors de la récupération du SMS
            await self._update_session_state(session_id, "FAILED", {"reason": str(e)})
            session["state"] = "FAILED"
        
        return self._session_to_poll_out(session)
    
    async def acknowledge(self, session_id: str, org_id: str, payload: OTPAcknowledgeIn) -> Dict[str, Any]:
        """
        Accuser réception d'un code OTP.
        
        Args:
            session_id: ID de la session
            org_id: ID de l'organisation
            payload: Données d'accusé de réception
            
        Returns:
            Dict de confirmation
        """
        session = await db["otp_sessions"].find_one({
            "_id": ObjectId(session_id),
            "org_id": org_id
        })
        
        if not session:
            raise ValueError("Session not found")
        
        if session["state"] != "DELIVERED_TO_ADMIN":
            raise ValueError(f"Cannot acknowledge session in state {session['state']}")
        
        # Log de l'action
        await self._log_session_action(session_id, payload.action, payload.note)
        
        return {"ok": True, "action": payload.action}
    
    async def apply(self, session_id: str, org_id: str, payload: OTPApplyIn) -> Dict[str, Any]:
        """
        Appliquer le résultat d'un code OTP.
        
        Args:
            session_id: ID de la session
            org_id: ID de l'organisation
            payload: Données d'application
            
        Returns:
            Dict avec l'état final
        """
        session = await db["otp_sessions"].find_one({
            "_id": ObjectId(session_id),
            "org_id": org_id
        })
        
        if not session:
            raise ValueError("Session not found")
        
        if session["state"] != "DELIVERED_TO_ADMIN":
            raise ValueError(f"Cannot apply session in state {session['state']}")
        
        # Déterminer l'état final
        final_state = "APPLIED_SUCCESS" if payload.outcome == "success" else "APPLIED_FAILED"
        
        # Mettre à jour la session
        now = datetime.now(timezone.utc)
        await db["otp_sessions"].update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "state": final_state,
                    "applied_at": now,
                    "updated_at": now,
                    "application_note": payload.note
                }
            }
        )
        
        # Broadcast WebSocket
        await self._broadcast_otp_applied(session_id, final_state, payload.note)
        
        # Log de l'action
        await self._log_session_action(session_id, f"applied_{payload.outcome}", payload.note)
        
        return {
            "ok": True,
            "session_id": session_id,
            "state": final_state,
            "applied_at": now.isoformat()
        }
    
    async def cancel(self, session_id: str, org_id: str, reason: str = "user_cancelled") -> Dict[str, Any]:
        """Annuler une session OTP."""
        session = await db["otp_sessions"].find_one({
            "_id": ObjectId(session_id),
            "org_id": org_id
        })
        
        if not session:
            raise ValueError("Session not found")
        
        if session["state"] in ["APPLIED_SUCCESS", "APPLIED_FAILED", "CANCELLED", "FAILED", "BANNED"]:
            raise ValueError(f"Cannot cancel session in state {session['state']}")
        
        # Annuler via l'adapter
        try:
            await self.adapter.cancel(session["provider_session_id"])
        except Exception as e:
            # Log l'erreur mais continuer
            await self._log_session_action(session_id, "cancel_error", str(e))
        
        # Mettre à jour la session
        await self._update_session_state(session_id, "CANCELLED", {"reason": reason})
        
        return {"ok": True, "state": "CANCELLED"}
    
    async def ban(self, session_id: str, org_id: str, reason: str = "fraud_detected") -> Dict[str, Any]:
        """Bannir une session OTP."""
        session = await db["otp_sessions"].find_one({
            "_id": ObjectId(session_id),
            "org_id": org_id
        })
        
        if not session:
            raise ValueError("Session not found")
        
        # Banner via l'adapter
        try:
            await self.adapter.ban(session["provider_session_id"])
        except Exception as e:
            # Log l'erreur mais continuer
            await self._log_session_action(session_id, "ban_error", str(e))
        
        # Mettre à jour la session
        await self._update_session_state(session_id, "BANNED", {"reason": reason})
        
        return {"ok": True, "state": "BANNED"}
    
    async def _update_session_state(self, session_id: str, state: OTPState, extra_data: Optional[Dict[str, Any]] = None):
        """Mettre à jour l'état d'une session."""
        update_data = {
            "state": state,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if extra_data:
            update_data.update(extra_data)
        
        await db["otp_sessions"].update_one(
            {"_id": ObjectId(session_id)},
            {"$set": update_data}
        )
    
    async def _log_session_action(self, session_id: str, action: str, note: Optional[str] = None):
        """Logger une action sur une session."""
        log_doc = {
            "session_id": session_id,
            "action": action,
            "note": note,
            "timestamp": datetime.now(timezone.utc)
        }
        
        await db["otp_session_logs"].insert_one(log_doc)
    
    async def _broadcast_otp_received(self, session_id: str, code_masked: str, message_preview: str):
        """Broadcast WebSocket pour code reçu."""
        try:
            from api.websockets.alerts import broadcast
            
            await broadcast({
                "event_type": "otp_code_received",
                "session_id": session_id,
                "data": {
                    "code_masked": code_masked,
                    "message_preview": message_preview
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            # Log l'erreur mais ne pas faire échouer la session
            print(f"WebSocket broadcast error: {e}")
    
    async def _broadcast_otp_applied(self, session_id: str, state: str, note: Optional[str] = None):
        """Broadcast WebSocket pour code appliqué."""
        try:
            from api.websockets.alerts import broadcast
            
            await broadcast({
                "event_type": "otp_applied",
                "session_id": session_id,
                "data": {
                    "state": state,
                    "note": note
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            print(f"WebSocket broadcast error: {e}")
    
    def _session_to_poll_out(self, session: Dict[str, Any]) -> OTPPollOut:
        """Convertir une session en OTPPollOut."""
        return OTPPollOut(
            session_id=str(session["_id"]),
            state=session["state"],
            code_masked=session.get("code_masked"),
            message_preview=session.get("message_preview"),
            provider=session.get("provider"),
            number=session.get("number"),
            updated_at=session["updated_at"],
            expires_at=session.get("expires_at")
        )
    
    async def get_session_stats(self, org_id: str, days: int = 7) -> Dict[str, Any]:
        """Récupérer les statistiques des sessions."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        pipeline = [
            {"$match": {"org_id": org_id, "created_at": {"$gte": cutoff}}},
            {"$group": {
                "_id": "$state",
                "count": {"$sum": 1}
            }}
        ]
        
        state_counts = await db["otp_sessions"].aggregate(pipeline).to_list(None)
        
        stats = {
            "total_sessions": sum(count["count"] for count in state_counts),
            "by_state": {count["_id"]: count["count"] for count in state_counts},
            "success_rate": 0.0,
            "period_days": days
        }
        
        # Calculer le taux de succès
        successful = stats["by_state"].get("APPLIED_SUCCESS", 0)
        total = stats["total_sessions"]
        if total > 0:
            stats["success_rate"] = successful / total
        
        return stats

# Instance globale du gestionnaire
otp_session_manager = OTPSessionManager()

# Fonctions de convenance
async def reserve_otp_session(payload: OTPReserveIn, org_id: str) -> OTPPollOut:
    """Réserver une session OTP."""
    return await otp_session_manager.reserve(payload, org_id)

async def poll_otp_session(session_id: str, org_id: str) -> OTPPollOut:
    """Poller une session OTP."""
    return await otp_session_manager.poll(session_id, org_id)

async def acknowledge_otp_session(session_id: str, org_id: str, payload: OTPAcknowledgeIn) -> Dict[str, Any]:
    """Accuser réception d'une session OTP."""
    return await otp_session_manager.acknowledge(session_id, org_id, payload)

async def apply_otp_session(session_id: str, org_id: str, payload: OTPApplyIn) -> Dict[str, Any]:
    """Appliquer le résultat d'une session OTP."""
    return await otp_session_manager.apply(session_id, org_id, payload)
