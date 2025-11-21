import pytest
from api.services.content_distributor.dispatcher import dispatch_content

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

    # Vérification du format de la réponse pour chaque plateforme
    for platform in platforms:
        assert platform in results, f"La plateforme '{platform}' n'est pas présente dans les résultats."
        res = results[platform]
        assert "status" in res or "error" in res, (
            f"Pour la plateforme '{platform}', aucune clé 'status' ou 'error' n'a été trouvée."
        )
