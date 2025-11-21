# api/routes/stats/timeline.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.services.analytics.timeline import generate_timeline_stats

router = APIRouter(prefix="/stats/timeline", tags=["stats"])

@router.get("/", response_model=Dict[str, List[Dict[str, Any]]])
async def get_timeline_stats(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Renvoie l’évolution des publications journalières (KPI) pour une agence ou une muse.

    - agency_id: identifiant de l'agence
    - muse_id: identifiant de la muse
    - start_date / end_date: plages de filtrage
    """
    try:
        timeline = await generate_timeline_stats(
            agency_id=agency_id,
            muse_id=muse_id,
            start_date=start_date,
            end_date=end_date
        )
        return {"timeline": timeline}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))