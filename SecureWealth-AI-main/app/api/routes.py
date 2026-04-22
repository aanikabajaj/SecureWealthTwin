"""
FastAPI router for SecureWealth Twin AI.
Modified to include GET /market-data for live financial snapshots.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from app.models.request import (
    AnalyzeUserRequest,
    ChatRequest,
    DecisionRequest,
    RiskCheckRequest,
    SimulateRequest,
)
from app.models.response import (
    AnalyzeUserResponse,
    ChatResponse,
    DecisionResponse,
    HealthResponse,
    MarketDataResponse,
    ProviderStatus,
    RiskCheckResponse,
    ScenarioResult,
    SimulateResponse,
    SubsystemStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Lazy singleton orchestrator
# ---------------------------------------------------------------------------

_orchestrator: Optional[object] = None 


def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = _build_orchestrator()
    return _orchestrator


def _build_orchestrator():
    from app.agents.orchestrator import OrchestratorAgent
    from app.agents.risk_assessment import RiskAssessmentAgent
    from app.agents.simulation import SimulationAgent
    from app.agents.wealth_advisor import WealthAdvisorAgent
    from app.engines.market_data import MarketDataClient
    from app.engines.rule_engine import RuleEngine
    from app.engines.wealth_intelligence import (
        BehaviorClassifier,
        NetWorthCalculator,
        TrendDetector,
    )
    from app.rag.knowledge_base import build_default_knowledge_base
    from app.rag.pipeline import RAGPipeline

    rule_engine = RuleEngine()
    behavior_classifier = BehaviorClassifier.load_or_train()
    trend_detector = TrendDetector()
    net_worth_calculator = NetWorthCalculator()
    market_data_client = MarketDataClient()

    kb = build_default_knowledge_base()
    rag_pipeline = RAGPipeline(vectorstore=kb.get_store())

    risk_agent = RiskAssessmentAgent(rule_engine=rule_engine)
    simulation_agent = SimulationAgent()
    wealth_advisor = WealthAdvisorAgent(
        behavior_classifier=behavior_classifier,
        trend_detector=trend_detector,
        net_worth_calculator=net_worth_calculator,
        rag_pipeline=rag_pipeline,
        market_data_client=market_data_client,
    )

    return OrchestratorAgent(
        wealth_advisor=wealth_advisor,
        risk_assessment=risk_agent,
        simulation=simulation_agent,
        rag_pipeline=rag_pipeline,
        market_data_client=market_data_client
    )


async def _run_with_timeout(fn, timeout: float, trace_id: str):
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, fn),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.warning("SLA exceeded trace_id=%s timeout=%.1fs", trace_id, timeout)
        raise HTTPException(status_code=504, detail={"error": "timeout", "trace_id": trace_id})


@router.post("/analyze-user", response_model=AnalyzeUserResponse)
async def analyze_user(request_body: AnalyzeUserRequest, request: Request):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    orchestrator = get_orchestrator()
    result = await _run_with_timeout(
        lambda: orchestrator.route_to_wealth_advisor(request_body, trace_id),
        timeout=10.0, trace_id=trace_id
    )
    return AnalyzeUserResponse(**result)


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(request_body: SimulateRequest, request: Request):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    orchestrator = get_orchestrator()
    result = await _run_with_timeout(
        lambda: orchestrator.route_to_simulation(request_body, trace_id),
        timeout=15.0, trace_id=trace_id
    )
    scenario_results = None
    if result.get("scenario_results"):
        scenario_results = [
            ScenarioResult(**s) if isinstance(s, dict) else s
            for s in result["scenario_results"]
        ]
    return SimulateResponse(
        trace_id=result["trace_id"],
        goal_achievement_probability=result["goal_achievement_probability"],
        projected_wealth_inr=result["projected_wealth_inr"],
        scenario_results=scenario_results,
        simulation_label=result["simulation_label"],
    )


@router.post("/risk-check", response_model=RiskCheckResponse)
async def risk_check(request_body: RiskCheckRequest, request: Request):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    orchestrator = get_orchestrator()
    result = await _run_with_timeout(
        lambda: orchestrator.route_to_risk_assessment(request_body, trace_id),
        timeout=3.0, trace_id=trace_id
    )
    return RiskCheckResponse(**result)


@router.post("/decision", response_model=DecisionResponse)
async def decision(request_body: DecisionRequest, request: Request):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    orchestrator = get_orchestrator()
    result = await _run_with_timeout(
        lambda: orchestrator.route_to_decision(request_body, trace_id),
        timeout=3.0, trace_id=trace_id
    )
    return DecisionResponse(**result)


@router.post("/chat", response_model=ChatResponse)
async def chat(request_body: ChatRequest, request: Request):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    orchestrator = get_orchestrator()
    result = await _run_with_timeout(
        lambda: orchestrator.route_to_conversational(request_body, trace_id),
        timeout=8.0, trace_id=trace_id
    )
    return ChatResponse(**result)


@router.get("/market-data", response_model=MarketDataResponse)
async def market_data(request: Request):
    """Fetch live market indices and financial snapshots."""
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    orchestrator = get_orchestrator()
    result = await _run_with_timeout(
        lambda: orchestrator.route_to_market_data(trace_id),
        timeout=5.0, trace_id=trace_id
    )
    return MarketDataResponse(**result)


@router.get("/health", response_model=HealthResponse)
async def health():
    import time
    subsystems: dict = {}
    providers: dict = {}

    try:
        start = time.monotonic()
        from app.engines.wealth_intelligence import NetWorthCalculator
        NetWorthCalculator()
        latency = (time.monotonic() - start) * 1000
        subsystems["wealth_intelligence"] = SubsystemStatus(status="up", latency_ms=round(latency, 2))
    except Exception:
        subsystems["wealth_intelligence"] = SubsystemStatus(status="down")

    try:
        from app.engines.market_data import MarketDataClient
        client = MarketDataClient()
        snapshot = client.fetch()
        status = "stale" if snapshot.is_stale else "up"
        providers["yahoo_finance"] = ProviderStatus(status=status, last_successful_fetch=snapshot.fetched_at if not snapshot.is_stale else None)
        providers["alpha_vantage"] = ProviderStatus(status="up")
    except Exception:
        providers["yahoo_finance"] = ProviderStatus(status="down")
        providers["alpha_vantage"] = ProviderStatus(status="down")

    return HealthResponse(status="healthy", subsystems=subsystems, market_data_providers=providers)
