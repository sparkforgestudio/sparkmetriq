# api/services/analytics/funnel_service.py
"""
Service d'analytics funnel et revenus.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from api.databases.databases import db

async def funnel_overview(tenant_id: str, date_from: datetime, date_to: datetime,
                          muse_id: Optional[str]=None, campaign: Optional[str]=None, channel: Optional[str]=None) -> Dict[str, Any]:
    match = {"tenant_id": tenant_id, "ts":{"$gte": date_from, "$lt": date_to}}
    if muse_id: match["muse_id"] = muse_id
    if campaign: match["meta.campaign"] = campaign
    if channel: match["source"] = channel

    rows = await db["events_funnel"].aggregate([
        {"$match": match},
        {"$group":{"_id":"$phase","count":{"$sum":1}}},
        {"$project":{"_id":0,"phase":"$_id","count":"$count"}}
    ]).to_list(None)

    M = {r["phase"]: r["count"] for r in rows}
    def g(k): return int(M.get(k,0))
    contact, lead, subscriber, payer, retained = g("contact"), g("lead"), g("subscriber"), g("payer"), g("retained")

    return {
        "contact": contact,
        "lead": lead,
        "subscriber": subscriber,
        "payer": payer,
        "retained": retained,
        "cr_contact_lead": (lead/contact) if contact else None,
        "cr_lead_subscriber": (subscriber/lead) if lead else None,
        "cr_subscriber_payer": (payer/subscriber) if subscriber else None,
    }

async def revenue_kpis(tenant_id: str, date_from: datetime, date_to: datetime,
                       muse_id: Optional[str]=None) -> Dict[str, Any]:
    match = {"tenant_id": tenant_id, "status":"confirmed", "ts":{"$gte":date_from,"$lt":date_to}}
    if muse_id: match["muse_id"] = muse_id

    rows = await db["payments"].aggregate([
        {"$match": match},
        {"$group":{"_id":"$user_hash","amount":{"$sum":"$amount"}}},
        {"$group":{"_id":None,"gmv":{"$sum":"$amount"},"payers":{"$sum":1},"ltv_mean":{"$avg":"$amount"}}},
        {"$project":{"_id":0}}
    ]).to_list(1)

    if not rows: return {"gmv":0.0,"payers":0,"arpu":None,"ltv_mean":None}
    r = rows[0]
    arpu = (r["gmv"]/r["payers"]) if r["payers"]>0 else None
    return {"gmv": float(r["gmv"]), "payers": r["payers"], "arpu": arpu, "ltv_mean": float(r["ltv_mean"]) if r["ltv_mean"] is not None else None}

async def ppv_kpis(tenant_id: str, date_from: datetime, date_to: datetime,
                   muse_id: Optional[str]=None) -> Dict[str, Any]:
    match = {"tenant_id": tenant_id, "ts":{"$gte":date_from,"$lt":date_to}}
    if muse_id: match["muse_id"] = muse_id

    agg = await db["ppv_logs"].aggregate([
        {"$match": match},
        {"$group":{
            "_id":"$status",
            "count":{"$sum":1},
            "avg_ticket":{"$avg":"$price"}
        }}
    ]).to_list(None)
    M = {r["_id"]: r for r in agg}
    sent = M.get("sent",{}).get("count",0)
    clicked = M.get("clicked",{}).get("count",0)
    paid = M.get("paid",{}).get("count",0)
    avg_ticket = M.get("paid",{}).get("avg_ticket", None)
    return {
        "sent": sent,
        "clicked": clicked,
        "paid": paid,
        "conv_rate_click": (clicked/sent) if sent else None,
        "conv_rate_paid": (paid/sent) if sent else None,
        "avg_ticket": float(avg_ticket) if avg_ticket is not None else None
    }
