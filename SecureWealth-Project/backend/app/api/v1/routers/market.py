from fastapi import APIRouter, Depends
from backend.app.services.ai_service import ai_service
from backend.app.middleware.auth_middleware import get_current_user
from backend.app.models.user import User

router = APIRouter()

@router.get("/live")
async def get_live_market(current_user: User = Depends(get_current_user)):
    """
    Returns verified live market indices from the AI engine.
    Fetches real ticker data for NIFTY, SENSEX, etc.
    """
    market_data = await ai_service.get_market_data()
    
    return {
        "status": "success",
        "data": {
            "indices": market_data.get("indices", []),
            "is_stale": market_data.get("is_stale", False),
            "last_updated": market_data.get("fetched_at")
        }
    }
