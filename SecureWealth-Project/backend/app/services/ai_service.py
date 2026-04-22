import logging
import httpx
from typing import Dict, Any, Optional
from backend.app.config import get_settings

logger = logging.getLogger("securewealth.ai")
settings = get_settings()

class AIService:
    """
    Bridge to the SecureWealth Twin AI service.
    Coordinates Wealth Intelligence (Advisory) and Cyber-Protection (Risk).
    """

    def __init__(self):
        self.base_url = getattr(settings, "AI_SERVICE_URL", "http://localhost:8001")
        self.timeout = 20.0
        # Simulated consent token for AI data processing
        self.default_consent = "CONSENT-SW-AI-2026"

    async def get_risk_score(self, action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call the AI Risk Assessment agent."""
        url = f"{self.base_url}/risk-check"
        try:
            user_id = str(payload.get("user_id", "anonymous"))
            amount = float(payload.get("current_value", 0))
            
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.post(url, json={
                    "consent_token": self.default_consent,
                    "user_id": user_id,
                    "action_type": action_type,
                    "action_amount_inr": amount,
                    "device_trust_status": True,
                    "first_time_action": True
                })
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"AI Risk Check failed: {e}")
            return {
                "risk_score": 0.5,
                "risk_label": "Unknown (Fallback)",
                "reasons": ["AI Service schema mismatch or error"]
            }

    async def get_wealth_recommendations(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Call the Wealth Advisor agent for personalized recommendations."""
        url = f"{self.base_url}/analyze-user"
        try:
            request_data = {
                "profile": {
                    **user_profile,
                    "consent_token": self.default_consent,
                    "user_id": str(user_profile.get("user_id", "unknown")),
                    "income_monthly_inr": user_profile.get("income_monthly_inr", 50000.0),
                    "risk_appetite": user_profile.get("risk_appetite", "moderate"),
                    "goals": user_profile.get("goals", []),
                    "assets": user_profile.get("assets", []),
                    "liabilities_inr": user_profile.get("liabilities_inr", 0.0),
                    "transactions": user_profile.get("transactions", [])
                }
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=request_data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"AI Recommendations failed: {e}")
            return {"recommendations": [], "disclaimer": "AI recommendations temporarily unavailable."}

    async def simulate_wealth(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the Simulation agent for wealth projections."""
        url = f"{self.base_url}/simulate"
        try:
            scenario_data["consent_token"] = self.default_consent
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=scenario_data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"AI Simulation failed: {e}")
            return {
                "goal_achievement_probability": 0.0,
                "projected_wealth_inr": 0.0,
                "simulation_label": "Error: Service Unavailable"
            }

    async def ask_ai(self, user_id: str, message: str, profile_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call the RAG Chat Advisor."""
        url = f"{self.base_url}/chat"
        try:
            payload = {
                "consent_token": self.default_consent,
                "user_id": str(user_id),
                "message": message,
                "profile_context": profile_context
            }
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"AI Chat failed: {e}")
            return {
                "answer": "I'm having trouble connecting to my knowledge base. Please try again in a moment.",
                "sources": [],
                "disclaimer": "AI Advisor temporarily offline."
            }

    async def get_market_data(self) -> Dict[str, Any]:
        """Fetch live market indices from the AI engine."""
        url = f"{self.base_url}/market-data"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch market data from AI: {e}")
            return {
                "equity_index": 0.0,
                "is_stale": True,
                "fetched_at": None
            }

# Global instance
ai_service = AIService()
