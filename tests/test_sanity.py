import os
from api.services.content_distributor.dispatcher import dispatch_content


def test_project_structure():
    required_dirs = [
        "apps/telegram_bot",
        "apps/instagram_bot",
        "apps/tiktok_bot",
        "apps/admin_panel",
        "services/api_backend",
        "services/user_mgmt",
        "services/payment_gateway",
        "services/content_manager",
        "services/chat_omnichannel"
    ]

    for directory in required_dirs:
        assert os.path.isdir(directory), f"Le dossier {directory} est manquant!"
