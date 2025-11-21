# api/routes/ppv_tracking.py
"""
Routes pour le tracking PPV (sent→clicked→paid).
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from api.databases.databases import db

router = APIRouter(prefix="/ppv", tags=["monetization"])

@router.get("/r/{token}")
async def redirect_ppv(token: str):
    """Redirection PPV avec tracking du clic."""
    log = await db["ppv_logs"].find_one({"payment.link_token": token})
    if not log:
        raise HTTPException(status_code=404, detail="Link not found")

    # mark clicked
    await db["ppv_logs"].update_one({"_id": log["_id"]}, {"$set":{"status":"clicked"}})
    url = log["payment"]["link_url"]
    return RedirectResponse(url=url)

# Webhook paid (provider-agnostic simulé)
@router.post("/webhook/paid/{token}")
async def webhook_paid(token: str):
    """Webhook pour marquer un PPV comme payé."""
    log = await db["ppv_logs"].find_one({"payment.link_token": token})
    if not log:
        raise HTTPException(status_code=404, detail="Link not found")

    await db["ppv_logs"].update_one({"_id": log["_id"]}, {"$set":{"status":"paid"}})

    # Optionnel: créer/mettre à jour un enregistrement dans `payments`
    # (mock minimal)
    await db["payments"].insert_one({
        "tenant_id": log.get("tenant_id"),
        "muse_id": log.get("muse_id"),
        "user_hash": log.get("user_id"),
        "status": "confirmed",
        "amount": log.get("price", 0.0),
        "ts": log.get("ts")  # ou utcnow()
    })
    return {"ok": True}



