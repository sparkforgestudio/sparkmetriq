# api/services/analytics/conversation_service.py
"""
Service d'analytics conversationnels.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from api.databases.databases import db

async def kpis_conversation(tenant_id: str, date_from: datetime, date_to: datetime,
                            muse_id: Optional[str]=None, agency_id: Optional[str]=None, channel: Optional[str]=None) -> Dict[str, Any]:
    match = {"tenant_id": tenant_id, "timestamp": {"$gte": date_from, "$lt": date_to}}
    if muse_id: match["muse_id"] = muse_id
    if agency_id: match["agency_id"] = agency_id
    if channel: match["channel"] = channel

    pipeline = [
        {"$match": match},
        {"$group":{
            "_id": "$conversation_id",
            "messages":{"$sum":1},
            "user_msgs":{"$sum":{"$cond":[{"$eq":["$role","user"]},1,0]}},
            "bot_msgs":{"$sum":{"$cond":[{"$eq":["$role","bot"]},1,0]}},
            "channels":{"$addToSet":"$channel"},
        }},
        {"$group":{
            "_id": None,
            "conversations":{"$sum":1},
            "messages":{"$sum":"$messages"},
            "user_msgs":{"$sum":"$user_msgs"},
            "bot_msgs":{"$sum":"$bot_msgs"},
            "channels_set":{"$push":"$channels"}
        }},
        {"$project":{
            "_id":0,
            "conversations":1,"messages":1,"user_msgs":1,"bot_msgs":1,
            "channels":{"$reduce":{"input":"$channels_set","initialValue":[],"in":{"$setUnion":["$$value","$$this"]}}}
        }}
    ]
    res = await db["chat_messages"].aggregate(pipeline).to_list(1)
    return res[0] if res else {"conversations":0,"messages":0,"user_msgs":0,"bot_msgs":0,"channels":[]}

async def response_time_stats(tenant_id: str, date_from: datetime, date_to: datetime,
                              muse_id: Optional[str]=None) -> Dict[str, Any]:
    match = {"tenant_id": tenant_id, "timestamp": {"$gte": date_from, "$lt": date_to}}
    if muse_id: match["muse_id"] = muse_id

    pipeline = [
        {"$match": match},
        {"$sort": {"conversation_id":1, "timestamp":1}},
        {"$group":{"_id":"$conversation_id","messages":{"$push":{"role":"$role","ts":"$timestamp"}}}},
        {"$project":{"pairs":{"$zip":{"inputs":["$messages","$messages"],"useLongestLength":False}}}},
        {"$unwind":"$pairs"},
        {"$project":{"a":{"$arrayElemAt":["$pairs",0]},"b":{"$arrayElemAt":["$pairs",1]}}},
        {"$match":{"a.role":"user","b.role":"bot"}},
        {"$project":{"rt_sec":{"$divide":[{"$subtract":["$b.ts","$a.ts"]},1000]}}},
        {"$group":{"_id":None,"avg_rt_sec":{"$avg":"$rt_sec"}}},
        {"$project":{"_id":0,"avg_rt_sec":1}}
    ]
    res = await db["chat_messages"].aggregate(pipeline).to_list(1)
    return res[0] if res else {"avg_rt_sec": None}
