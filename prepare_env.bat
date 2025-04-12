@echo off
echo 🔧 Préparation de l’environnement musai-musemgmt-platform...

REM 1. Déplacement du .env si nécessaire
IF EXIST .env\.env (
    move .env\.env .env
    echo ✅ Fichier .env déplacé à la racine
)

REM 2. Création de pytest.ini
echo [pytest]> pytest.ini
echo pythonpath = ./api>> pytest.ini
echo addopts = --tb=short -q>> pytest.ini
echo ✅ Fichier pytest.ini créé

REM 3. Création du dossier .vscode et du launch.json
IF NOT EXIST .vscode (
    mkdir .vscode
)

echo {> .vscode\launch.json
echo   "version": "0.2.0",>> .vscode\launch.json
echo   "configurations": [>> .vscode\launch.json
echo     {>> .vscode\launch.json
echo       "name": "Launch API (FastAPI)",>> .vscode\launch.json
echo       "type": "python",>> .vscode\launch.json
echo       "request": "launch",>> .vscode\launch.json
echo       "program": "${workspaceFolder}/venv/Scripts/uvicorn.exe",>> .vscode\launch.json
echo       "args": [>> .vscode\launch.json
echo         "api.main:app",>> .vscode\launch.json
echo         "--reload",>> .vscode\launch.json
echo         "--port", "8000"]>> .vscode\launch.json
echo       ,>> .vscode\launch.json
echo       "console": "integratedTerminal",>> .vscode\launch.json
echo       "envFile": "${workspaceFolder}/.env">> .vscode\launch.json
echo     }>> .vscode\launch.json
echo   ]>> .vscode\launch.json
echo }>> .vscode\launch.json
echo ✅ launch.json généré

REM 4. Nettoyage du dossier .env
IF EXIST .env (
    rmdir /S /Q .env
    echo 🧹 Dossier .env supprimé
)

echo ✅ Préparation terminée !
pause
