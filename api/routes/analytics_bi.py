# api/routes/analytics_bi.py
"""
Routes FastAPI pour les analytics BI (funnel, revenus, prévisions).
"""

from fastapi import APIRouter, Depends, Query
from datetime import datetime
from typing import Optional
from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.analytics import FunnelOverview, RevenueKPIs, PPVKPIs, ForecastResponse
from api.services.analytics.funnel_service import funnel_overview, revenue_kpis, ppv_kpis
from api.services.analytics.forecast_service import forecast_messages, forecast_gmv

router = APIRouter(prefix="/analytics/bi", tags=["analytics"])

@router.get("/funnel", response_model=FunnelOverview)
async def get_funnel(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    muse_id: Optional[str] = None,
    campaign: Optional[str] = None,
    channel: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
):
    return await funnel_overview(current_user.id, date_from, date_to, muse_id, campaign, channel)

@router.get("/revenue", response_model=RevenueKPIs)
async def get_revenue(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    muse_id: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
):
    return await revenue_kpis(current_user.id, date_from, date_to, muse_id)

@router.get("/ppv", response_model=PPVKPIs)
async def get_ppv_kpis(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    muse_id: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
):
    return await ppv_kpis(current_user.id, date_from, date_to, muse_id)

@router.get("/forecast/messages", response_model=ForecastResponse)
async def get_forecast_messages(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    horizon: int = Query(7, ge=1, le=30),
    muse_id: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
):
    return await forecast_messages(current_user.id, date_from, date_to, horizon, muse_id)

@router.get("/forecast/gmv", response_model=ForecastResponse)
async def get_forecast_gmv(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    horizon: int = Query(7, ge=1, le=30),
    muse_id: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
):
    return await forecast_gmv(current_user.id, date_from, date_to, horizon, muse_id)
