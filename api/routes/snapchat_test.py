from fastapi import APIRouter, HTTPException
from api.services.content_distributor.connectors.snapchat import publish_to_snapchat

router = APIRouter()

@router.post("/test/snapchat", response_model=dict)
async def test_snapchat_connector():
    """
    Endpoint pour tester la publication sur Snapchat via le connecteur.
    Renvoie le résultat de la publication sous forme de dictionnaire.
    """
    fake_content = {
        "media_url": "https://example.com/test-snap.jpg",
        "caption": "Test publication Snapchat"
    }
    fake_model_info = {
        "agency_id": "test_agency",
        "muse_id": "test_muse",
        "access_token": "test_token"
    }

    try:
        result = await publish_to_snapchat(fake_content, fake_model_info)
        return {"status": "success", "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
