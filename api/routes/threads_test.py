from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from services.content_distributor.connectors.threads import publish_to_threads
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

class ThreadsPost(BaseModel):
    caption: str
    media_url: HttpUrl

@router.post("/test")
async def test_threads_post(post: ThreadsPost):
    """
    Endpoint pour tester la publication sur Threads.
    """
    try:
        response = publish_to_threads(caption=post.caption, media_url=str(post.media_url))
        return {"status": "success", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
