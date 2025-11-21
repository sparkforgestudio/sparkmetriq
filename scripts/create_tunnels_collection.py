from pymongo import MongoClient
from datetime import datetime

# Connexion à la base MongoDB locale
client = MongoClient("mongodb://localhost:27017")
db = client["musemgmtdb"]

# Index pour faciliter les recherches
db["tunnels"].create_index([("agency_id", 1), ("model_id", 1)])

# Exemple d'entrée (à supprimer si non souhaité)
example_tunnel = {
    "agency_id": "musai",
    "model_id": "melissa",
    "platforms": ["instagram", "tiktok", "telegram"],
    "schedule": {
        "hour": "10:00",
        "timezone": "Europe/Paris"
    },
    "content_tags": ["teasing", "conversion"],
    "preferred_format": "story",
    "call_to_action": "dm",  # ex: dm, linktree, join telegram, etc.
    "created_at": utcnow()
}

# Insertion de test
db["tunnels"].insert_one(example_tunnel)

print("✅ Collection 'tunnels' créée avec index et document d’exemple.")
