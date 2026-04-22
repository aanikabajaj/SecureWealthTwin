"""
SecureWealth Twin — Physical Assets Router.

Endpoints
─────────
POST   /api/v1/assets                   Add a new physical asset
GET    /api/v1/assets                   List all current assets
GET    /api/v1/assets/summary           Category-level totals
GET    /api/v1/assets/{id}              Get a single asset
PATCH  /api/v1/assets/{id}             Update asset (creates new valuation snapshot)
DELETE /api/v1/assets/{id}             Soft-retire an asset
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import get_db
from backend.app.middleware.auth_middleware import get_current_user
from backend.app.models.user import User
from backend.app.schemas.asset_schemas import (
    AssetSummaryByCategory,
    PhysicalAssetCreateRequest,
    PhysicalAssetResponse,
    PhysicalAssetUpdateRequest,
)
from backend.app.services.asset_service import PhysicalAssetService

router = APIRouter()


@router.post(
    "",
    response_model=PhysicalAssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new physical asset",
)
async def add_asset(
    req: PhysicalAssetCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a real-world asset — property, gold, vehicle, jewellery, etc. —
    to the user's wealth profile.
    Set `include_in_networth=true` to have it counted in the net-worth computation.
    """
    svc = PhysicalAssetService(db)
    try:
        return await svc.add_asset(current_user.id, req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "",
    response_model=list[PhysicalAssetResponse],
    summary="List all current physical assets",
)
async def list_assets(
    category: str | None = Query(None, description="Filter by asset category"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PhysicalAssetService(db)
    try:
        return await svc.list_assets(current_user.id, category=category)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/summary",
    response_model=list[AssetSummaryByCategory],
    summary="Category-level asset totals",
)
async def asset_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns total value, effective value, and outstanding loans per category."""
    svc = PhysicalAssetService(db)
    return await svc.category_summary(current_user.id)


@router.get(
    "/{asset_id}",
    response_model=PhysicalAssetResponse,
    summary="Get a single physical asset",
)
async def get_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PhysicalAssetService(db)
    try:
        return await svc.get_asset(current_user.id, asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch(
    "/{asset_id}",
    response_model=PhysicalAssetResponse,
    summary="Update an asset's valuation (creates a new snapshot)",
)
async def update_asset(
    asset_id: uuid.UUID,
    req: PhysicalAssetUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Updates asset details by retiring the old record and creating a new
    current snapshot. Valuation history is preserved automatically.
    """
    svc = PhysicalAssetService(db)
    try:
        return await svc.update_asset(current_user.id, asset_id, req)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an asset from the active list",
)
async def delete_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PhysicalAssetService(db)
    try:
        await svc.delete_asset(current_user.id, asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
