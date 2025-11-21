# api/services/analytics/forecast_service.py
"""
Service de prévisions (forecasts) naïf et robuste.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from api.databases.databases import db

def _linear_forecast(values: List[float], horizon: int) -> List[float]:
    n = len(values)
    if n < 2:
        last = values[-1] if values else 0.0
        return [float(last)] * horizon
    t = list(range(n))
    st, sy = sum(t), sum(values)
    stt = sum(i*i for i in t)
    sty = sum(i*v for i, v in zip(t, values))
    denom = (n*stt - st*st) or 1
    a = (n*sty - st*sy) / denom
    b = (sy - a*st) / n
    start = n
    preds = []
    for i in range(horizon):
        yhat = a*(start+i) + b
        preds.append(float(max(0.0, yhat)))
    return preds

async def _series_daily(col_name: str, date_field: str, value_expr: Dict[str, Any],
                        tenant_id: str, date_from: datetime, date_to: datetime,
                        muse_id: Optional[str]=None):
    match = {"tenant_id": tenant_id, date_field: {"$gte": date_from, "$lt": date_to}}
    if muse_id: match["muse_id"] = muse_id

    pipeline = [
        {"$match": match},
        {"$group":{
            "_id":{"$dateToString":{"format":"%Y-%m-%d","date":f"${date_field}"}},
            "val": value_expr
        }},
        {"$sort":{"_id":1}}
    ]
    rows = await db[col_name].aggregate(pipeline).to_list(None)
    days = [r["_id"] for r in rows]
    vals = [float(r["val"]) for r in rows]
    return days, vals

async def forecast_messages(tenant_id: str, date_from: datetime, date_to: datetime, horizon: int=7, muse_id: Optional[str]=None):
    days, vals = await _series_daily("chat_messages", "timestamp", {"$sum":1}, tenant_id, date_from, date_to, muse_id)
    preds = _linear_forecast(vals, horizon)
    return {"series":[{"day":f"+{i+1}","yhat":p} for i,p in enumerate(preds)], "model":"naive-linear"}

async def forecast_gmv(tenant_id: str, date_from: datetime, date_to: datetime, horizon: int=7, muse_id: Optional[str]=None):
    days, vals = await _series_daily("payments", "ts", {"$sum":"$amount"}, tenant_id, date_from, date_to, muse_id)
    preds = _linear_forecast(vals, horizon)
    return {"series":[{"day":f"+{i+1}","yhat":p} for i,p in enumerate(preds)], "model":"naive-linear"}
