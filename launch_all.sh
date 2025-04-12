#!/bin/bash

echo "🚀 Démarrage des services MusAI..."

# 1. Activer l’environnement virtuel Python
source venv/bin/activate

# 2. Lancer FastAPI (backend)
echo "▶️ Lancement de l'API FastAPI sur :8000..."
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload > logs/uvicorn.log 2>&1 &

# 3. Lancer le service de planification
echo "⏱️ Lancement du scheduler..."
nohup python scripts/scheduler.py > logs/scheduler.log 2>&1 &

# 4. Lancer le frontend Next.js (admin_panel)
echo "🖥️ Lancement de l'interface admin (Next.js)..."
cd frontend/admin_panel

# Vérifier si pnpm est installé
if ! command -v pnpm &> /dev/null; then
    echo "❌ pnpm n'est pas installé. Installation..."
    npm install -g pnpm
fi

pnpm install
nohup pnpm dev > ../../logs/nextjs.log 2>&1 &

# 5. Retour à la racine
cd ../../

echo "✅ Tous les services sont en cours d'exécution. Consultez les fichiers logs dans /logs"
