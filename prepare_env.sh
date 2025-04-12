#!/bin/bash

echo "🔧 Préparation de l’environnement musai-musemgmt-platform..."

# 1. Déplacer .env/.env vers la racine
if [ -f "./.env/.env" ]; then
  mv .env/.env .env
  echo "✅ Fichier .env déplacé à la racine"
fi

# 2. Créer pytest.ini
cat <<EOF > pytest.ini
[pytest]
pythonpath = ./api
addopts = --tb=short -q
EOF
echo "✅ Fichier pytest.ini créé"

# 3. Créer .vscode/launch.json
mkdir -p .vscode
cat <<EOF > .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch API (FastAPI)",
      "type": "python",
      "request": "launch",
      "program": "\${workspaceFolder}/venv/Scripts/uvicorn.exe",
      "args": [
        "api.main:app",
        "--reload",
        "--port", "8000"
      ],
      "console": "integratedTerminal",
      "envFile": "\${workspaceFolder}/.env"
    }
  ]
}
EOF
echo "✅ Fichier .vscode/launch.json généré"

# 4. Supprimer dossier .env/ s’il existe
if [ -d "./.env" ]; then
  rm -rf .env
  echo "🧹 Dossier .env supprimé (inutile)"
fi

echo "✅ Tous les fichiers sont en place. Tu peux lancer FastAPI avec la config VSCode."
