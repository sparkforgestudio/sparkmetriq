# api/services/analytics/materialize_jobs.py
"""
Jobs d'agrégation pour la matérialisation journalière des données analytics.
"""

from datetime import datetime
from typing import Optional
from api.databases.databases import db

def _day_bounds(day: str):
    # day: "YYYY-MM-DD"
    start = datetime.fromisoformat(day + "T00:00:00")
    end = datetime.fromisoformat(day + "T23:59:59.999")
    return start, end

async def materialize_conversation_daily(tenant_id: str, day: str, muse_id: Optional[str]=None):
    start, end = _day_bounds(day)
    match = {"tenant_id": tenant_id, "timestamp":{"$gte": start, "$lte": end}}
    if muse_id: match["muse_id"] = muse_id

    rows = await db["chat_messages"].aggregate([
        {"$match": match},
        {"$group":{
            "_id": None,
            "messages":{"$sum":1},
            "user_msgs":{"$sum":{"$cond":[{"$eq":["$role","user"]},1,0]}},
            "bot_msgs":{"$sum":{"$cond":[{"$eq":["$role","bot"]},1,0]}}
        }},
        {"$project":{"_id":0,"messages":1,"user_msgs":1,"bot_msgs":1}}
    ]).to_list(1)

    doc = rows[0] if rows else {"messages":0,"user_msgs":0,"bot_msgs":0}
    await db["conversation_daily"].update_one(
        {"tenant_id": tenant_id, "muse_id": muse_id, "day": day},
        {"$set": doc}, upsert=True
    )

async def materialize_revenue_daily(tenant_id: str, day: str, muse_id: Optional[str]=None):
    start, end = _day_bounds(day)
    match = {"tenant_id": tenant_id, "status":"confirmed", "ts":{"$gte":start,"$lte":end}}
    if muse_id: match["muse_id"] = muse_id

    rows = await db["payments"].aggregate([
        {"$match": match},
        {"$group":{"_id": None, "gmv":{"$sum":"$amount"}, "payers":{"$addToSet":"$user_hash"}}},
        {"$project":{"_id":0,"gmv":1,"payers":{"$size":"$payers"}}}
    ]).to_list(1)

    doc = rows[0] if rows else {"gmv":0.0,"payers":0}
    await db["revenue_daily"].update_one(
        {"tenant_id": tenant_id, "muse_id": muse_id, "day": day},
        {"$set": doc}, upsert=True
    )

async def materialize_ppv_daily(tenant_id: str, day: str, muse_id: Optional[str]=None):
    start, end = _day_bounds(day)
    match = {"tenant_id": tenant_id, "ts":{"$gte":start,"$lte":end}}
    if muse_id: match["muse_id"] = muse_id

    rows = await db["ppv_logs"].aggregate([
        {"$match": match},
        {"$group":{"_id":"$status","count":{"$sum":1},"avg_ticket":{"$avg":"$price"}}}
    ]).to_list(None)
    M = {r["_id"]: r for r in rows}
    doc = {
        "sent": M.get("sent",{}).get("count",0),
        "clicked": M.get("clicked",{}).get("count",0),
        "paid": M.get("paid",{}).get("count",0),
        "avg_ticket": M.get("paid",{}).get("avg_ticket", None)
    }
    await db["ppv_daily"].update_one(
        {"tenant_id": tenant_id, "muse_id": muse_id, "day": day},
        {"$set": doc}, upsert=True
    )
