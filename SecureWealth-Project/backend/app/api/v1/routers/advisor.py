"""
SecureWealth Twin — Wealth Advisor Router.
Bridges the main wealth data with the AI Intelligence microservice.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import get_db
from backend.app.middleware.auth_middleware import get_current_user
from backend.app.models.user import User
from backend.app.services.ai_service import ai_service
from backend.app.services.asset_service import PhysicalAssetService

router = APIRouter()

@router.get("/recommendations", summary="Get AI-powered wealth recommendations")
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyzes the user's full financial picture and returns AI-driven strategic advice.
    """
    asset_svc = PhysicalAssetService(db)
    
    # 1. Gather User's Wealth Profile
    # In a full implementation, we'd pull from Account Aggregator as well.
    # For now, we use the Registered Physical Assets and User Info.
    assets = await asset_svc.list_assets(current_user.id)
    
    # Format for AI service
    profile_for_ai = {
        "user_id": str(current_user.id),
        "full_name": current_user.full_name,
        "income_monthly_inr": 150000.0, # Simulated/from profile
        "risk_appetite": "moderate",
        "goals": ["Retirement", "Wealth Growth"],
        "assets": [
            {
                "asset_type": "property" if a.category == "real_estate" else "gold" if a.category == "gold" else "financial_instrument",
                "value_inr": float(a.current_value),
                "description": a.name
            } for a in assets
        ],
        "liabilities_inr": sum(float(a.outstanding_loan) for a in assets),
        "transactions": [] # To be integrated with AA
    }
    
    # 2. Call the AI Intelligence Service
    recommendations = await ai_service.get_wealth_recommendations(profile_for_ai)
    
    return recommendations
