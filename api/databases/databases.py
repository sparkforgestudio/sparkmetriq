from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()  # Charger les variables d'environnement

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "musemgmtdb")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def connect_db():
    try:
        client.admin.command("ping")
        print("✅ Connexion MongoDB établie")
    except Exception as e:
        print("❌ Erreur de connexion à MongoDB:", e)
