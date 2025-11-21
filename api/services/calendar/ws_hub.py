# api/services/calendar/ws_hub.py
"""
Hub WebSocket pour le calendrier en temps réel.
"""

import logging
from typing import Set, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class CalendarWSHub:
    """Hub WebSocket pour les notifications calendrier."""
    
    def __init__(self):
        """Initialise le hub."""
        # org_id -> set(websockets)
        self.clients: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, org_id: str, websocket: WebSocket):
        """
        Connecte un client WebSocket.
        
        Args:
            org_id: ID de l'organisation
            websocket: Connexion WebSocket
        """
        if org_id not in self.clients:
            self.clients[org_id] = set()
        
        self.clients[org_id].add(websocket)
        logger.info(f"WebSocket connected: org_id={org_id}, total_clients={len(self.clients[org_id])}")
    
    def disconnect(self, org_id: str, websocket: WebSocket):
        """
        Déconnecte un client WebSocket.
        
        Args:
            org_id: ID de l'organisation
            websocket: Connexion WebSocket
        """
        if org_id in self.clients:
            self.clients[org_id].discard(websocket)
            
            # Nettoyer si plus de clients
            if not self.clients[org_id]:
                del self.clients[org_id]
            
            logger.info(f"WebSocket disconnected: org_id={org_id}")
    
    async def broadcast(self, org_id: str, event: str, payload: Dict[str, Any]):
        """
        Diffuse un événement à tous les clients d'une organisation.
        
        Args:
            org_id: ID de l'organisation
            event: Type d'événement
            payload: Données de l'événement
        """
        if org_id not in self.clients:
            return
        
        message = {
            "event": event,
            "payload": payload
        }
        
        # Diffuser à tous les clients
        disconnected = set()
        for ws in self.clients[org_id]:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending WS message: {e}")
                disconnected.add(ws)
        
        # Nettoyer les connexions fermées
        for ws in disconnected:
            self.disconnect(org_id, ws)
        
        logger.debug(
            f"Broadcast to {len(self.clients[org_id])} clients: "
            f"org_id={org_id}, event={event}"
        )


# Instance globale
hub = CalendarWSHub()



