"""
SecureWealth Twin — Physical Assets Router.
"""

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import get_db
from backend.app.middleware.auth_middleware import get_current_user
from backend.app.models.user import User
from backend.app.schemas.asset_schemas import (
    AssetSummaryByCategory, PhysicalAssetCreateRequest,
    PhysicalAssetResponse, PhysicalAssetUpdateRequest,
)
from backend.app.services.asset_service import PhysicalAssetService
from backend.app.services.ai_service import ai_service
from backend.app.services.blockchain_service import blockchain_service

router = APIRouter()
logger = logging.getLogger("securewealth.assets")

@router.post(
    "", response_model=PhysicalAssetResponse, status_code=status.HTTP_201_CREATED,
    summary="Register a new physical asset",
)
async def add_asset(
    req: PhysicalAssetCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    # Optional header to bypass challenge (simulated for the "Verify" flow)
    x_security_token: str | None = Query(None, alias="security_token")
):
    """
    Add property, gold, vehicle, jewellery, or any other real-world asset.
    
    🛡️ ENFORCES WEALTH PROTECTION SHIELD:
    If AI risk score >= 70, the action is BLOCKED unless a security_token is provided.
    """
    svc = PhysicalAssetService(db)
    
    # 1. 🛡️ Perform AI Risk Check
    risk_assessment = await ai_service.get_risk_score(
        action_type="ADD_ASSET",
        payload={**req.model_dump(mode='json'), "user_id": str(current_user.id)}
    )
    
    risk_score = risk_assessment.get("risk_score", 0)
    risk_label = risk_assessment.get("risk_label", "Low")
    
    # 2. 🔗 Log Intent to Blockchain (Always logged, even if blocked)
    await blockchain_service.log_action(
        action_type="ASSET_REGISTRATION_INTENT",
        payload={
            "user_id": str(current_user.id),
            "asset_name": req.name,
            "valuation": float(req.current_value),
            "risk_score": risk_score
        },
        risk_label=risk_label
    )
    
    # 3. 🛑 Wealth Protection Enforcement
    # If risk is high and no bypass token is present, challenge the user
    if risk_score >= 70 and not x_security_token:
        logger.warning(f"BLOCKING high-risk action for user {current_user.id}. Score: {risk_score}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "SECURITY_CHALLENGE_REQUIRED",
                "message": "High-risk activity detected. Additional verification required.",
                "risk_score": risk_score,
                "reasons": risk_assessment.get("reasons", ["Anomalous transaction pattern"])
            }
        )

    # 4. 💾 Proceed with DB storage if low risk or verified
    try:
        asset = await svc.add_asset(current_user.id, req)
        
        # Log successful execution to blockchain
        await blockchain_service.log_action(
            action_type="ASSET_REGISTRATION_SUCCESS",
            payload={"asset_id": str(asset.id)},
            risk_label=risk_label
        )
        
        return asset
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[PhysicalAssetResponse], summary="List all current physical assets")
async def list_assets(
    category: str | None = Query(None, description="Filter by: real_estate | gold | vehicle | jewellery | art_collectible | business | other"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PhysicalAssetService(db)
    try:
        return await svc.list_assets(current_user.id, category=category)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/summary", response_model=list[AssetSummaryByCategory], summary="Category-level asset totals")
async def asset_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PhysicalAssetService(db)
    return await svc.category_summary(current_user.id)


@router.get("/{asset_id}", response_model=PhysicalAssetResponse, summary="Get a single physical asset")
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


@router.patch("/{asset_id}", response_model=PhysicalAssetResponse, summary="Update asset valuation")
async def update_asset(
    asset_id: uuid.UUID,
    req: PhysicalAssetUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PhysicalAssetService(db)
    try:
        return await svc.update_asset(current_user.id, asset_id, req)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove an asset")
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
