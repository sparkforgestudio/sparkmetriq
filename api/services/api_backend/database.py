from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"  # Change selon ta config
DB_NAME = "musai_db"

client = AsyncIOMotorClient(MONGO_URI)
database = client[DB_NAME]
