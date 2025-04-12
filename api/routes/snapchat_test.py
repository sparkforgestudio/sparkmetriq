from fastapi import APIRouter
from services.content_distributor.snapchat import publish_to_snapchat

router = APIRouter()

@router.post("/test/snapchat")
async def test_snapchat_connector():
    fake_content = {
        "media_url": "https://example.com/test-snap.jpg",
        "caption": "Test publication Snapchat"
    }
    fake_model_info = {
        "agency_id": "test_agency",
        "muse_id": "test_muse",
        "access_token": "test_token"
    }
    result = await publish_to_snapchat(fake_content, fake_model_info)
    return result
