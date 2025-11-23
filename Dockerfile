# Dockerfile multi-stage pour SparkMetrics Platform (Backend API uniquement)
# Le frontend Next.js doit être servi séparément ou via un reverse proxy

# Stage 1: Build du backend FastAPI
FROM python:3.11-slim as backend-builder

WORKDIR /app

# Installer les dépendances système nécessaires pour compiler certaines dépendances Python
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Image finale
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système minimales (curl pour healthcheck)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les dépendances Python depuis le builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copier le code backend
COPY api/ ./api/
COPY scripts/ ./scripts/
COPY pytest.ini pyproject.toml ./

# Créer un utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Variables d'environnement par défaut
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Exposer le port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/healthz || exit 1

# Commande par défaut (peut être surchargée)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Copier tous les fichiers de requirements (core + modules optionnels)
COPY requirements.txt requirements-ai-marketing.txt requirements-cloudphone.txt ./
