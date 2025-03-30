import os

# Définition des dossiers à créer
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
    ".github/workflows"
]

# Définition des fichiers vides à créer
files = {
    "README.md": "# MusAI Management Platform\n",
    "requirements.txt": "flask\nflask-cors\npython-dotenv\nrequests\npython-telegram-bot\n",
    ".gitignore": "__pycache__/\n.env\n*.log\n",
    "tests/test_sanity.py": """import os

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
""",
    ".github/workflows/ci.yml": """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Structure Tests
        run: pytest tests/test_sanity.py
"""
}

# Création des dossiers
for directory in directories:
    os.makedirs(directory, exist_ok=True)

# Création des fichiers avec contenu de base
for file_path, content in files.items():
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print("📁 Structure du projet créée avec succès ! 🚀")
