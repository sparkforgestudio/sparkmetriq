# tests/conftest.py
import os
import sys
from dotenv import load_dotenv
import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

# ── STUB NOWPAYMENTS ────────────────────────────────────────────────────────────
import api.services.payment_gateway.nowpayments as nowp

async def _stub_generate_payment_link(payment_id, payload):
    # Pour passer le test, on retourne une URL qui commence par https://pay.now/
    return f"https://pay.now/{payment_id}"

async def _stub_process_webhook_notification(payment_id, status):
    from bson import ObjectId
    from api.databases.databases import db
    await db["payments"].update_one(
        {"_id": ObjectId(payment_id)},
        {"$set": {"status": status}}
    )

nowp.generate_payment_link = _stub_generate_payment_link
nowp.process_webhook_notification = _stub_process_webhook_notification
# ───

# 1) Charger .env et forcer TESTING
load_dotenv()
os.environ["TESTING"] = "true"

# 2) Définir l'URI et le nom de la BDD de test
TEST_DB_URI = os.getenv(
    "TEST_DB_URI",
    "mongodb://localhost:27017/musemgmtdb_test"
)
TEST_DB_NAME = TEST_DB_URI.rsplit("/", 1)[-1]

# Surcharger les variables que votre code de prod utilise
os.environ["MONGO_URI"] = TEST_DB_URI
os.environ["DB_NAME"] = TEST_DB_NAME

# 3) Ajouter la racine du projet pour pouvoir importer `app`
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

# 4) Importer l’app **après** avoir configuré les deux ENV VARS
from api.main import app  # noqa: E402

# 5) Fournir un client HTTP synchronisé
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

# 6) Fixture pour obtenir des headers d’authentification
@pytest.fixture
def auth_headers(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    # Comme on purge la BDD avant chaque test, cet utilisateur n'existe jamais
    assert resp.status_code == 200, (
        f"Échec de l'enregistrement en test : "
        f"{resp.status_code} {resp.text}"
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# 7) Purger la BDD **de test** avant chaque test (autouse)
@pytest.fixture(autouse=True)
def clear_db():
    mongo = MongoClient(TEST_DB_URI)
    db = mongo.get_database(TEST_DB_NAME)
    for coll in (
        "users",
        "payments",
        "ppv_contents",
        "public_contents",
        "tunnels",
        "scheduled_tasks",
    ):
        db[coll].delete_many({})
    yield
    mongo.close()
