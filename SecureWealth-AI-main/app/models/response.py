"""
Pydantic response models for SecureWealth Twin AI API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional, Any

from pydantic import BaseModel


class ShapFeature(BaseModel):
    feature_name: str
    shap_value: float
    direction: Literal["positive", "negative"]


class ShapExplanation(BaseModel):
    top_features: List[ShapFeature]


class SignalContribution(BaseModel):
    signal_name: str
    contribution: float
    description: str


class DocumentSource(BaseModel):
    title: str
    origin: str
    similarity_score: float


class ScenarioResult(BaseModel):
    label: str
    goal_achievement_probability: float
    projected_wealth_inr: float


class AnalyzeUserResponse(BaseModel):
    trace_id: str
    spending_category: str
    net_worth_inr: float
    income_trend: str
    expense_trend: str
    recommendations: List[str]
    disclaimer: str


class SimulateResponse(BaseModel):
    trace_id: str
    goal_achievement_probability: float
    projected_wealth_inr: float
    simulation_label: str


class RiskCheckResponse(BaseModel):
    trace_id: str
    risk_score: float
    risk_label: str
    reasons: List[SignalContribution]


class DecisionResponse(BaseModel):
    trace_id: str
    risk_score: float
    decision: str
    reasons: List[SignalContribution]


class ChatResponse(BaseModel):
    trace_id: str
    answer: str
    sources: List[DocumentSource]
    disclaimer: str


class MarketIndexData(BaseModel):
    name: str
    value: float
    change: str
    change_raw: float
    trend: str


class MarketDataResponse(BaseModel):
    trace_id: str
    fetched_at: datetime
    indices: List[MarketIndexData]
    is_stale: bool


class SubsystemStatus(BaseModel):
    status: Literal["up", "down"]
    latency_ms: Optional[float] = None


class ProviderStatus(BaseModel):
    status: Literal["up", "down", "stale"]
    last_successful_fetch: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
    subsystems: Dict[str, SubsystemStatus]
    market_data_providers: Dict[str, ProviderStatus]
