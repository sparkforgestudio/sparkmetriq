from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, HttpUrl
from services.content_distributor.connectors.instagram import upload_instagram_photo
from api.routes.auths import router as auths_router
from api.routes.users import router as users_router
from api.routes.payments import router as payments_router
from api.routes.webhooks.payments_webhook import router as webhook_router
from api.routes.ppv import router as ppv_router
from api.routes.public_contents import router as public_router
from api.routes.dispatcher import router as dispatcher_router
from api.routes.tunnels_test import router as tunnels_router
from api.routes.instagram_test import router as instagram_router
from api.routes.threads_test import router as threads_router
from api.routes.snapchat_test import router as snapchat_test_router
from api.routes.scheduler import router as scheduler_router
router = APIRouter()

class InstagramPost(BaseModel):
    image_url: HttpUrl
    caption: str = ""

@router.post("/test")
async def test_instagram_post(data: InstagramPost):
    try:
        response = await upload_instagram_photo(
            image_url=data.image_url,
            caption=data.caption
        )
        return {
            "status": "success",
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
