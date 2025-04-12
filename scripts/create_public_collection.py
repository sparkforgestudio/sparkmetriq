# 📄 scripts/create_publics_collection.py

from pymongo import MongoClient, ASCENDING, DESCENDING

# Connexion à MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["musemgmtdb"]

# Création de la collection s'il n'existe pas encore
collection_name = "public_contents"
if collection_name not in db.list_collection_names():
    db.create_collection(collection_name)
    print(f"✅ Collection '{collection_name}' créée avec succès.")
else:
    print(f"ℹ️ Collection '{collection_name}' existe déjà.")

# Création d’un index combiné
db[collection_name].create_index(
    [("agency_id", ASCENDING), ("muse_id", ASCENDING), ("created_at", DESCENDING)],
    name="agency_muse_date_index"
)

print("✅ Index 'agency_muse_date_index' créé avec succès.")
