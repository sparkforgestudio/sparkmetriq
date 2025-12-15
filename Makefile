# -------- Config de base --------
SHELL := /bin/bash
PY := python
PIP := pip
UVICORN := uvicorn
APP_MODULE := api.main:app
HOST := 0.0.0.0
PORT := 8000

# Charge .env si présent (Unix / Git Bash)
ifneq (,$(wildcard .env))
include .env
export
endif

# Activer le venv si tu utilises .venv
VENV ?= .venv
ACTIVATE := source $(VENV)/Scripts/activate 2>/dev/null || source $(VENV)/bin/activate

# -------- Cibles phony --------
.PHONY: help setup install upgrade env-check dev run test test-quick test-one \
        lint format typecheck \
        db-indexes db-info db-core-info db-bi-info db-seed db-clean \
        health curl-root curl-docs \
        dc-up dc-down dc-restart dc-logs docker-build docker-push \
        freeze clean reset

help:
	@echo "Make targets principaux :"
	@echo "  setup            - Crée l'environnement virtuel et installe les deps"
	@echo "  install          - Installe les dépendances (requirements.txt/pyproject)"
	@echo "  upgrade          - Met à jour pip et outils de base"
	@echo "  env-check        - Vérifie la présence des variables d'env essentielles"
	@echo "  dev              - Lance l'API en dev (reload)"
	@echo "  run              - Lance l'API sans reload"
	@echo "  test             - Lance la suite de tests avec flags TESTING"
	@echo "  test-quick       - Tests rapides (sans docker, -q)"
	@echo "  test-one         - TEST_PATH=... make test-one (ex: TEST_PATH=chat_tests/...py)"
	@echo "  lint             - Ruff (lint)"
	@echo "  format           - Black + Ruff --fix"
	@echo "  typecheck        - Mypy"
	@echo "  db-indexes       - Crée/maj les index Core+BI via startup"
	@echo "  db-info          - Affiche les infos DB (collections clés)"
	@echo "  health           - Ping endpoints santé"
	@echo "  dc-up            - docker compose up -d"
	@echo "  dc-down          - docker compose down"
	@echo "  dc-restart       - down puis up"
	@echo "  dc-logs          - logs compose"
	@echo "  docker-build     - Build image docker"
	@echo "  docker-push      - Push image docker"
	@echo "  freeze           - Gèle les requirements"
	@echo "  clean            - Nettoyage fichiers temporaires"
	@echo "  reset            - Clean + suppression caches & artefacts"

# -------- Environnement & dépendances --------
setup:
	@$(PY) -m venv $(VENV)
	@$(ACTIVATE) && $(PIP) install -U pip wheel setuptools
	@echo "✅ Venv prêt dans $(VENV)."

install:
	@$(ACTIVATE) && if [ -f requirements.txt ]; then $(PIP) install -r requirements.txt; fi
	@$(ACTIVATE) && if [ -f pyproject.toml ]; then $(PIP) install -e .; fi
	@echo "✅ Dépendances installées."

upgrade:
	@$(ACTIVATE) && $(PIP) install -U pip setuptools wheel
	@$(ACTIVATE) && $(PIP) install -U black ruff mypy pytest pytest-asyncio httpx
	@echo "✅ Outils mis à jour."

env-check:
	@echo "🔎 Vérification de quelques variables d'env clés..."
	@bash -lc '\
	    missing=0; \
	    for k in MONGO_URI DB_NAME_CORE MONGO_URI_BI DB_NAME_BI SECURITY_SECRET_KEY; do \
	      v=$${!k}; \
	      if [ -z "$$v" ]; then echo "❌ Manquante: $$k"; missing=1; else echo "✅ $$k ok"; fi; \
	    done; \
	    if [ $$missing -eq 1 ]; then exit 1; fi \
	'

# -------- Lancement de l'API --------
dev:
	@$(ACTIVATE) && $(UVICORN) $(APP_MODULE) --host $(HOST) --port $(PORT) --reload

run:
	@$(ACTIVATE) && $(UVICORN) $(APP_MODULE) --host $(HOST) --port $(PORT)

# -------- Tests --------
test:
	@echo "🧪 Tests avec TESTING=true"
	@TESTING=true $(ACTIVATE) && pytest -q

test-quick:
	@TESTING=true $(ACTIVATE) && pytest -q -k "not slow"

# Ex: make test-one TEST_PATH=chat_tests/services/test_send_existing_conversation.py::test_post_chat_send_reuses_existing_conversation -v -s
test-one:
	@if [ -z "$(TEST_PATH)" ]; then echo "❌ Fournis TEST_PATH=..."; exit 1; fi
	@TESTING=true $(ACTIVATE) && pytest $(TEST_PATH) -v -s

# -------- Qualité code --------
lint:
	@$(ACTIVATE) && ruff check api chat_tests

format:
	@$(ACTIVATE) && black api chat_tests
	@$(ACTIVATE) && ruff check --fix api chat_tests

typecheck:
	@$(ACTIVATE) && mypy api || true

# -------- MongoDB (Core + BI) --------
db-indexes:
	@echo "🚀 Création/MàJ des index via startup (Core + BI)..."
	@$(ACTIVATE) && $(UVICORN) api.main:app --host 127.0.0.1 --port 8765 --loop asyncio --http httptools --log-level warning &
	@sleep 2
	@curl -sf http://127.0.0.1:8765/health/mongo >/dev/null && echo "✅ Mongo connecté" || (echo "❌ Mongo KO" && exit 1)
	@pkill -f "uvicorn api.main:app" || true
	@echo "✅ Index créés (Core & BI)."

db-info:
	@curl -s "http://127.0.0.1:8000/health/db-info?collections=users&collections=chat_messages&collections=events_funnel" | jq .

db-core-info:
	@echo "Core: $(MONGO_URI)/$(DB_NAME_CORE)"
db-bi-info:
	@echo "BI: $(MONGO_URI_BI)/$(DB_NAME_BI)"

# Optionnel: peupler des données de démo
db-seed:
	@$(ACTIVATE) && $(PY) scripts/seed_demo.py

db-clean:
	@$(ACTIVATE) && $(PY) - <<'PY'
	from api.databases.databases import db_core, db_bi
	for c in ["users","chat_messages","payments","conversation_recaps","message_templates","campaigns","outbox_messages"]:
	    db_core[c].delete_many({})
	for c in ["events_funnel","conversation_daily","revenue_daily","ppv_daily","scheduled_drafts"]:
	    db_bi[c].delete_many({})
	print("✅ DB clean (Core & BI).")
	PY

# -------- Santé --------
health:
	@curl -sSf http://127.0.0.1:8000/health | jq .
curl-root:
	@curl -sSf http://127.0.0.1:8000/ | jq .
curl-docs:
	@echo "➜ Ouvre http://127.0.0.1:8000/docs"

# -------- Docker/Compose --------
dc-up:
	docker compose up -d

dc-down:
	docker compose down

dc-restart: dc-down dc-up

dc-logs:
	docker compose logs -f --tail=200

docker-build:
	docker build -t musai-platform:latest .

docker-push:
	@echo "⚠️ Configure le registry/login avant de pousser"; exit 1

# -------- Divers --------
freeze:
	@$(ACTIVATE) && pip freeze > requirements.txt
	@echo "✅ requirements.txt mis à jour."

clean:
	@find . -name "__pycache__" -type d -exec rm -rf {} +
	@find . -name ".pytest_cache" -type d -exec rm -rf {} +
	@find . -name "*.pyc" -delete
	@echo "✅ Clean caches."

reset: clean
	@rm -rf .mypy_cache .ruff_cache || true
	@echo "✅ Reset caches."

.PHONY: lint-architecture
lint-architecture:
	./scripts/ci/check_core_imports.sh
	./scripts/ci/check_core_vocabulary.sh /tmp/core_blacklist_tokens.txt
	python ./scripts/check_workspace_consistency.py
