import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")  # Access token Meta
THREADS_USER_ID = os.getenv("THREADS_USER_ID")      # ID utilisateur Threads (lié à Instagram Business)

# Charger les variables d'environnement
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "mysecret")
ALGORITHM = "HS256"

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "musemgmtdb"

client = AsyncIOMotorClient(MONGO_URI)
database = client[DB_NAME]
