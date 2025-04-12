import os

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"📁 Dossier créé : {path}")
    else:
        print(f"✅ Dossier déjà existant : {path}")

def setup_project():
    directories = [
        "apps/telegram_bot",
        "apps/instagram_bot",
        "apps/tiktok_bot",
        "apps/admin_panel",
        "services/api_backend",
        "services/user_mgmt",
        "services/payment_gateway",
        "services/content_manager",
        "services/chat_omnichannel",
        "tests",
        "config/tenants",
        "database/migrations",
        "scripts"
    ]
    
    for directory in directories:
        create_directory(directory)

    print("\n🚀 Structure du projet configurée avec succès !")

if __name__ == "__main__":
    setup_project()
