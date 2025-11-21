# api/routes/analytics_conversations.py
"""
Routes FastAPI pour les analytics conversationnels.
"""

from fastapi import APIRouter, Depends, Query
from datetime import datetime
from typing import Optional
from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.analytics import ConversationAnalyticsResponse, ConversationKPIs, ResponseTimeStats
from api.services.analytics.conversation_service import kpis_conversation, response_time_stats

router = APIRouter(prefix="/analytics/conversations", tags=["analytics"])

@router.get("/kpis", response_model=ConversationAnalyticsResponse)
async def conv_kpis(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    muse_id: Optional[str] = None,
    agency_id: Optional[str] = None,
    channel: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
):
    base = await kpis_conversation(current_user.id, date_from, date_to, muse_id, agency_id, channel)
    rts = await response_time_stats(current_user.id, date_from, date_to, muse_id)
    return {"kpis": ConversationKPIs(**base), "response_time": ResponseTimeStats(**rts)}
