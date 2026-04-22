from fastapi import APIRouter, Depends
from typing import List, Dict

from backend.app.middleware.auth_middleware import get_current_user
from backend.app.models.user import User
from backend.app.services.blockchain_service import blockchain_service

router = APIRouter()

@router.get("/", summary="Get immutable audit trail from blockchain")
async def get_audit_trail(
    current_user: User = Depends(get_current_user),
    limit: int = 10
):
    """
    Returns the last 'n' entries from the blockchain audit log.
    In a real scenario, this would verify the integrity of each log entry.
    """
    # Only allow customers to see their own (or admins to see all)
    # For now, return the global simulated audit trail
    logs = await blockchain_service.get_audit_trail(limit=limit)
    return {
        "status": "success",
        "provider": "Ethereum (Simulated)",
        "logs": logs
    }
