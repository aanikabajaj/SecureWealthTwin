"""
SecureWealth Twin — Scenario Simulator Router.
Bridges the main project with the AI Simulation Agent.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import get_db
from backend.app.middleware.auth_middleware import get_current_user
from backend.app.models.user import User
from backend.app.services.ai_service import ai_service
from backend.app.services.asset_service import PhysicalAssetService

router = APIRouter()

class WhatIfScenario(BaseModel):
    label: str
    monthly_savings_rate_inr: Optional[float] = None
    investment_allocation: Optional[Dict[str, float]] = None
    time_horizon_months: Optional[int] = None

class SimulationRequest(BaseModel):
    monthly_savings_rate_inr: float
    investment_allocation: Dict[str, float]
    target_goal_inr: float
    time_horizon_months: int
    what_if_scenarios: Optional[List[WhatIfScenario]] = None

@router.post("/run", summary="Run a wealth projection simulation")
async def run_simulation(
    req: SimulationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calls the AI Simulation Agent to project future wealth.
    """
    asset_svc = PhysicalAssetService(db)
    
    # 1. Calculate Current Net Worth
    assets = await asset_svc.list_assets(current_user.id)
    total_assets = sum(float(a.current_value) for a in assets)
    
    # 2. Prepare Payload for AI
    # investment_allocation must sum to 1.0 (handled by AI service validation)
    ai_payload = {
        "current_assets_inr": total_assets,
        "monthly_savings_rate_inr": req.monthly_savings_rate_inr,
        "investment_allocation": req.investment_allocation,
        "target_goal_inr": req.target_goal_inr,
        "time_horizon_months": req.time_horizon_months,
        "what_if_scenarios": [s.model_dump() for s in req.what_if_scenarios] if req.what_if_scenarios else []
    }
    
    # 3. Call AI Simulation Service
    try:
        result = await ai_service.simulate_wealth(ai_payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")
