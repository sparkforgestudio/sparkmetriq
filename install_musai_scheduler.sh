#!/bin/bash

# === Configuration ===
SERVICE_NAME=musai-scheduler
USER=musai  # À adapter à ton utilisateur système réel
WORKDIR=/home/musai/musai-musemgtm-platform
PYTHON_EXEC=$WORKDIR/venv/bin/python
ENTRYPOINT=start_scheduler.py

# === Création du service systemd ===
echo "📦 Création du service $SERVICE_NAME..."

SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Musai Content Scheduler
After=network.target

[Service]
User=$USER
WorkingDirectory=$WORKDIR
ExecStart=$PYTHON_EXEC $ENTRYPOINT
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL

# === Activation du service ===
echo "🔄 Rechargement de systemd..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

echo "✅ Activation du service au démarrage..."
sudo systemctl enable $SERVICE_NAME

echo "🚀 Démarrage du service..."
sudo systemctl restart $SERVICE_NAME

echo "📡 Statut du service :"
sudo systemctl status $SERVICE_NAME --no-pager

echo ""
echo "📘 Pour suivre les logs en temps réel :"
echo "journalctl -u $SERVICE_NAME -f"
