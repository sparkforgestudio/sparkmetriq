@echo off
echo 🌐 Starting Musai Platform Services...

REM Activer l’environnement virtuel Python
call venv\Scripts\activate

REM Lancer FastAPI backend
start cmd /k "uvicorn api.main:app --reload --port 8000"

REM Lancer le scheduler (exécute le script Python)
start cmd /k "python scripts/scheduler.py"

REM Lancer le panneau admin (Next.js)
cd frontend\admin_panel
call pnpm install
start cmd /k "pnpm dev"

cd ../..

echo ✅ Tous les services ont été lancés dans des consoles séparées.
pause
