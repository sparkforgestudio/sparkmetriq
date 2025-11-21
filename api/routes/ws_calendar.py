# api/routes/ws_calendar.py
"""
Route WebSocket pour le calendrier en temps réel.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from api.services.calendar.ws_hub import hub

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/calendar")
async def ws_calendar(websocket: WebSocket, org_id: str = Query(..., description="ID de l'organisation")):
    """
    Endpoint WebSocket pour les notifications calendrier en temps réel.
    
    Args:
        websocket: Connexion WebSocket
        org_id: ID de l'organisation
    """
    await websocket.accept()
    await hub.connect(org_id, websocket)
    
    try:
        while True:
            # Keepalive: recevoir des messages (ping/pong ou autres)
            data = await websocket.receive_text()
            # Optionnel: traiter les messages clients (pings, subscriptions, etc.)
            # Pour MVP, on ignore les messages entrants
    except WebSocketDisconnect:
        hub.disconnect(org_id, websocket)
    except Exception as e:
        # En cas d'erreur, déconnecter proprement
        hub.disconnect(org_id, websocket)
        raise



