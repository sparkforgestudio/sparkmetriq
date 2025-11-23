# api/services/collab/ws.py
"""
Manager WebSocket pour la collaboration en temps réel.
"""

from typing import Dict, Set
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class CollabWSHub:
    """
    Hub WebSocket pour diffuser les événements de collaboration.
    Organisé par org_id pour isoler les organisations.
    """
    
    def __init__(self):
        self.org_clients: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, org_id: str, ws: WebSocket):
        """
        Connecte un client WebSocket à un org_id.
        
        Args:
            org_id: ID de l'organisation
            ws: WebSocket client
        """
        await ws.accept()
        if org_id not in self.org_clients:
            self.org_clients[org_id] = set()
        self.org_clients[org_id].add(ws)
        logger.info(f"WebSocket connected for org {org_id} (total: {len(self.org_clients[org_id])})")
    
    def disconnect(self, org_id: str, ws: WebSocket):
        """
        Déconnecte un client WebSocket.
        
        Args:
            org_id: ID de l'organisation
            ws: WebSocket client
        """
        if org_id in self.org_clients:
            self.org_clients[org_id].discard(ws)
            if len(self.org_clients[org_id]) == 0:
                del self.org_clients[org_id]
        logger.info(f"WebSocket disconnected for org {org_id}")
    
    async def broadcast(self, org_id: str, message: dict):
        """
        Diffuse un message à tous les clients connectés d'une organisation.
        
        Args:
            org_id: ID de l'organisation
            message: Message à diffuser (dict JSON-serializable)
        """
        clients = self.org_clients.get(org_id, set())
        if not clients:
            return
        
        disconnected = []
        for ws in list(clients):
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending WS message to org {org_id}: {e}")
                disconnected.append(ws)
        
        # Nettoyer les clients déconnectés
        for ws in disconnected:
            self.disconnect(org_id, ws)


# Instance globale du hub
hub = CollabWSHub()




