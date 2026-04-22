"""
Orchestrator Agent — routes incoming requests to the appropriate sub-agent.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.agents.risk_assessment import RiskAssessmentAgent
from app.agents.simulation import SimulationAgent
from app.agents.wealth_advisor import WealthAdvisorAgent
from app.engines.market_data import MarketDataClient
from app.models.request import (
    AnalyzeUserRequest,
    ChatRequest,
    DecisionRequest,
    RiskCheckRequest,
    SimulateRequest,
)
from app.rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    def __init__(
        self,
        wealth_advisor: WealthAdvisorAgent,
        risk_assessment: RiskAssessmentAgent,
        simulation: SimulationAgent,
        rag_pipeline: RAGPipeline,
        market_data_client: Optional[MarketDataClient] = None,
    ) -> None:
        self._wealth_advisor = wealth_advisor
        self._risk_assessment = risk_assessment
        self._simulation = simulation
        self._rag_pipeline = rag_pipeline
        self._market_data_client = market_data_client

    def route_to_wealth_advisor(self, request: AnalyzeUserRequest, trace_id: str) -> dict:
        result = self._wealth_advisor.analyze(request)
        result["trace_id"] = trace_id
        return result

    def route_to_risk_assessment(self, request: RiskCheckRequest, trace_id: str) -> dict:
        result = self._risk_assessment.assess(request)
        result["trace_id"] = trace_id
        return result

    def route_to_decision(self, request: DecisionRequest, trace_id: str) -> dict:
        result = self._risk_assessment.decide(request)
        result["trace_id"] = trace_id
        return result

    def route_to_simulation(self, request: SimulateRequest, trace_id: str) -> dict:
        result = self._simulation.simulate(request)
        result["trace_id"] = trace_id
        return result

    def route_to_conversational(self, request: ChatRequest, trace_id: str) -> dict:
        rag_result = self._rag_pipeline.answer(request.message)
        return {
            "answer": rag_result["answer"],
            "sources": rag_result["sources"],
            "trace_id": trace_id,
            "disclaimer": "Informational only."
        }

    def route_to_market_data(self, trace_id: str) -> dict:
        """Fetch accurate real-time market data."""
        if self._market_data_client is None:
            self._market_data_client = MarketDataClient()
            
        indices_data = self._market_data_client.fetch_live_indices()
        return {
            "trace_id": trace_id,
            "fetched_at": self._market_data_client.get_last_updated(),
            "indices": indices_data,
            "is_stale": False
        }
