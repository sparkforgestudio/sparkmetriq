import pytest
import asyncio
from api.routes.auths import router as auths_router
from api.routes.users import router as users_router
from api.routes.payments import router as payments_router
from api.routes.webhooks.payments_webhook import router as webhook_router
from api.routes.ppv import router as ppv_router
from api.routes.public_contents import router as public_router
from api.routes.dispatcher import router as dispatcher_router
from api.routes.tunnels import router as tunnels_router
from api.routes.instagram_test import router as instagram_router
from api.routes.threads_test import router as threads_router
from api.routes.snapchat_test import router as snapchat_test_router
from api.routes.scheduler import router as scheduler_router
from services.content_distributor.onlyfans import publish_to_onlyfans

# Activer le mode async pour pytest
pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_dispatch_to_all_platforms():
    fake_content = {
        "media": [
            {
                "type": "image",
                "url": "https://example.com/image.jpg"
            }
        ],
        "caption": "Test Caption"
    }

    fake_model_info = {
        "access_token": "test_token",
        "page_id": "123456",
        "thread_token": "fake_thread_token",
        "session_cookie": "fake_cookie",
        "telegram_token": "fake_telegram_token",
        "onlyfans_auth": "fake_of_cookie"
    }

    platforms = [
        "instagram", "tiktok", "threads", "snapchat", "reddit",
        "twitter", "telegram", "facebook", "onlyfans"
    ]

    results = await dispatch_content(fake_content, platforms, fake_model_info)

    # Vérification du format de la réponse
    for platform in platforms:
        assert platform in results
        assert "status" in results[platform] or "error" in results[platform]
