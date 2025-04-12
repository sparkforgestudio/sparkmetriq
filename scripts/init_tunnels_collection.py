from pymongo import MongoClient
from datetime import datetime

# Connexion MongoDB locale
client = MongoClient("mongodb://localhost:27017")
db = client["musemgmtdb"]

# Création de la collection "tunnels" si elle n'existe pas déjà
if "tunnels" not in db.list_collection_names():
    db.create_collection("tunnels")

# Création d'un index pour optimiser les recherches
db.tunnels.create_index([("agency_id", 1), ("muse_id", 1), ("created_at", -1)])

print("✅ Collection 'tunnels' initialisée avec succès.")
