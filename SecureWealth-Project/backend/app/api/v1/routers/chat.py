"""
SecureWealth Twin — AI Chat Advisor Router.
Bridges the main project with the AI RAG Chat system.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.services.ai_service import ai_service
from app.services.asset_service import PhysicalAssetService

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

def map_asset_type(category: str) -> str:
    """Map backend categories to AI service AssetEntry types."""
    mapping = {
        "real_estate": "property",
        "gold": "gold",
        "vehicle": "vehicle",
        "jewellery": "gold", # Jewellery maps to gold for AI logic
        "art_collectible": "property", # Treat high-value art as property
        "business": "property",
    }
    return mapping.get(category.lower(), "financial_instrument")

@router.post("/ask", summary="Ask the AI Wealth Advisor a question")
async def ask_advisor(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Asks a question to the AI RAG Advisor with current user context.
    """
    asset_svc = PhysicalAssetService(db)
    
    # 1. Fetch current assets for context
    assets = await asset_svc.list_assets(current_user.id)
    assets_list = [
        {
            "asset_type": map_asset_type(a.category.value),
            "value_inr": float(a.current_value),
            "description": f"{a.name}: {a.description or ''}"
        } for a in assets
    ]
    
    # 2. Build profile context
    profile_context = {
        "user_id": str(current_user.id),
        "consent_token": "CONSENT-SW-AI-2026", # Pass token to nested profile
        "income_monthly_inr": 75000.0,
        "risk_appetite": "moderate",
        "goals": ["Retirement", "Home Purchase"],
        "assets": assets_list,
        "liabilities_inr": 0.0,
        "transactions": []
    }
    
    # 3. Call AI Chat Service
    try:
        result = await ai_service.ask_ai(
            user_id=str(current_user.id),
            message=req.message,
            profile_context=profile_context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
