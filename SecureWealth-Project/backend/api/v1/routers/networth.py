"""
SecureWealth Twin — Net Worth Router.

Endpoints
─────────
GET    /api/v1/networth                 Latest net-worth snapshot
POST   /api/v1/networth/recompute       Trigger a fresh recompute
GET    /api/v1/networth/history         Time-series of past snapshots
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import get_db
from backend.app.middleware.auth_middleware import get_current_user
from backend.app.models.user import User
from backend.app.schemas.asset_schemas import (
    NetWorthRecomputeResponse,
    NetWorthResponse,
)
from backend.app.services.asset_service import NetWorthService

router = APIRouter()


@router.get(
    "",
    response_model=NetWorthResponse,
    summary="Get the latest net-worth snapshot",
)
async def get_networth(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the most recent net-worth computation including breakdown by:
    - Primary bank (financial assets)
    - AA-linked accounts (other banks)
    - Physical assets (property, gold, vehicles, etc.)
    - Total liabilities
    """
    svc = NetWorthService(db)
    result = await svc.get_latest(current_user.id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="No net-worth snapshot found. Call POST /recompute first.",
        )
    return result


@router.post(
    "/recompute",
    response_model=NetWorthRecomputeResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger a full net-worth recomputation",
)
async def recompute_networth(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Pulls the latest data from:
    - WealthProfile (primary bank savings + investments)
    - AALinkedAccount (other banks via Account Aggregator)
    - PhysicalAsset (user-declared assets)

    Creates an immutable NetWorthSnapshot and syncs WealthProfile.net_worth.
    """
    svc = NetWorthService(db)
    try:
        return await svc.recompute(current_user.id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Recompute failed: {exc}")


@router.get(
    "/history",
    response_model=list[NetWorthResponse],
    summary="Net-worth history (time-series)",
)
async def networth_history(
    limit: int = Query(12, ge=1, le=60, description="Number of snapshots to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the last N net-worth snapshots in reverse chronological order.
    Useful for rendering a trend chart in the dashboard.
    """
    svc = NetWorthService(db)
    return await svc.get_history(current_user.id, limit=limit)
