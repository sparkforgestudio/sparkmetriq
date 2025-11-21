from datetime import datetime, timedelta
from api.databases.databases import db
from typing import Optional, List, Dict
from bson.son import SON

async def generate_timeline_stats(
    agency_id: Optional[str],
    muse_id: Optional[str],
    start_date: Optional[datetime],
    end_date: Optional[datetime]
) -> List[Dict]:

    start = start_date or (utcnow() - timedelta(days=30))
    end = end_date or utcnow()

    match_stage = {
        "created_at": {"$gte": start, "$lte": end}
    }
    if agency_id:
        match_stage["agency_id"] = agency_id
    if muse_id:
        match_stage["muse_id"] = muse_id

    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}
            },
            "posts": {"$sum": 1},
            "success": {
                "$sum": {
                    "$cond": [{"$eq": ["$status", "success"]}, 1, 0]
                }
            },
            "errors": {
                "$sum": {
                    "$cond": [{"$eq": ["$status", "error"]}, 1, 0]
                }
            }
        }},
        {"$sort": SON([("_id.date", 1)])}
    ]

    logs = await db["platform_logs"].aggregate(pipeline).to_list(length=None)

    timeline = []
    for entry in logs:
        date = entry["_id"]["date"]
        posts = entry.get("posts", 0)
        success = entry.get("success", 0)
        errors = entry.get("errors", 0)
        success_rate = round((success / posts) * 100, 2) if posts else 0

        timeline.append({
            "date": date,
            "posts": posts,
            "success_rate": success_rate,
            "errors": errors
        })

    return timeline
