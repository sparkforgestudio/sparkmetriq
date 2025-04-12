from fastapi import FastAPI
from api.routes import auths, users, bots, analytics
from api.database import connect_db

app = FastAPI(title="MuseMGM API")

# Connexion à MongoDB
connect_db()

# Ajouter les routes
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(auths.router, prefix="/auth", tags=["Authentication"])
app.include_router(bots.router, prefix="/bots", tags=["Bots"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

@app.get("/")
async def root():
    return {"message": "Welcome to MuseMGM API"}

