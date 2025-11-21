from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from api.services.content_distributor.connectors.threads import publish_to_threads

router = APIRouter(prefix="/threads-test")

class ThreadsTestRequest(BaseModel):
    caption: str
    media_url: HttpUrl

@router.post("/test", response_model=dict)
async def test_threads_post(payload: ThreadsTestRequest):
    """
    Endpoint pour tester la publication sur Threads.
    """
    # Préparer le contenu attendu par le connecteur
    content = {
        "caption": payload.caption,
        "media": [{"url": str(payload.media_url), "type": "photo"}]
    }
    # Modèle d'information utilisateur/agence (valeurs factices pour le test)
    model_info = {
        "agency_id": "test_agency",
        "muse_id": "test_muse",
        # Ajoutez ici d'autres champs si nécessaire (e.g., tokens)
    }
    try:
        # Appel du connecteur Threads
        result = await publish_to_threads(content, model_info)
        return {"status": "success", "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
