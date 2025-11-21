from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from io import StringIO
import csv
from api.databases.databases import db
from api.core.auth import is_admin
from datetime import datetime
from typing import Literal
from bson import ObjectId

router = APIRouter()

@router.get("/export")
async def export_stats_csv(
    entity: Literal["agencies", "muses"] = Query(..., description="Exporter les stats des agences ou des muses"),
    admin=Depends(is_admin)
):
    # Définition de la clé et du champ groupé selon le type
    group_field = "$agency_id" if entity == "agencies" else "$muse_id"
    label = "agency_id" if entity == "agencies" else "muse_id"

    # Pipeline MongoDB
    pipeline = [
        {
            "$group": {
                "_id": group_field,
                "total_tasks": {"$sum": 1},
                "success": {"$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}},
                "errors": {"$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}},
            }
        },
        {
            "$project": {
                "_id": 0,
                label: "$_id",
                "total_tasks": 1,
                "success": 1,
                "errors": 1
            }
        }
    ]

    data = await db["platform_logs"].aggregate(pipeline).to_list(length=500)

    # Écriture du CSV dans une mémoire tampon
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=[label, "total_tasks", "success", "errors"])
    writer.writeheader()
    for row in data:
        writer.writerow(row)

    # Format du nom de fichier
    filename = f"{entity}_stats_{utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
