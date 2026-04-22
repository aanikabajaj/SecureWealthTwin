"""
SecureWealth Twin — Physical Asset & Net Worth Pydantic Schemas.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator

from backend.app.models.physical_asset import (
    AssetCategory,
    OwnershipType,
    ValuationMethod,
)


# ── Physical Asset Schemas ────────────────────────────────────────────────────

class PhysicalAssetCreateRequest(BaseModel):
    """Body for POST /api/v1/assets."""

    category: AssetCategory
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None

    current_value: Decimal = Field(..., gt=0, description="Current market value in INR")
    purchase_value: Decimal | None = Field(None, ge=0)
    purchase_date: date | None = None

    valuation_date: date
    valuation_method: ValuationMethod = ValuationMethod.SELF_DECLARED

    outstanding_loan: Decimal = Field(default=Decimal("0"), ge=0)

    ownership_type: OwnershipType = OwnershipType.SOLE
    ownership_percentage: Decimal = Field(
        default=Decimal("100.00"), gt=0, le=Decimal("100.00")
    )

    metadata_json: dict[str, Any] | None = None
    document_urls: list[str] | None = None
    include_in_networth: bool = True

    @model_validator(mode="after")
    def validate_purchase_date(self) -> "PhysicalAssetCreateRequest":
        if self.purchase_date and self.purchase_date > self.valuation_date:
            raise ValueError("purchase_date cannot be after valuation_date")
        return self


class PhysicalAssetUpdateRequest(BaseModel):
    """Body for PATCH /api/v1/assets/{id} — partial update."""

    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    current_value: Decimal | None = Field(None, gt=0)
    valuation_date: date | None = None
    valuation_method: ValuationMethod | None = None
    outstanding_loan: Decimal | None = Field(None, ge=0)
    ownership_percentage: Decimal | None = Field(None, gt=0, le=Decimal("100.00"))
    metadata_json: dict[str, Any] | None = None
    document_urls: list[str] | None = None
    include_in_networth: bool | None = None


class PhysicalAssetResponse(BaseModel):
    """Response for a single physical asset."""

    id: uuid.UUID
    user_id: uuid.UUID
    category: AssetCategory
    name: str
    description: str | None
    current_value: Decimal
    purchase_value: Decimal | None
    purchase_date: date | None
    valuation_date: date
    valuation_method: ValuationMethod
    outstanding_loan: Decimal
    ownership_type: OwnershipType
    ownership_percentage: Decimal
    effective_value: Decimal         # computed property from model
    unrealised_gain: Decimal | None  # computed property from model
    metadata_json: dict[str, Any] | None
    document_urls: list[str] | None
    include_in_networth: bool
    is_current: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetSummaryByCategory(BaseModel):
    """Subtotals per asset category."""

    category: AssetCategory
    total_value: Decimal
    total_effective_value: Decimal
    total_outstanding_loan: Decimal
    count: int


# ── Net Worth Schemas ─────────────────────────────────────────────────────────

class NetWorthResponse(BaseModel):
    """Full net-worth response from GET /api/v1/networth."""

    user_id: uuid.UUID
    snapshot_id: uuid.UUID
    computed_at: datetime

    # Buckets
    financial_assets: Decimal     # Primary bank data
    aa_assets: Decimal            # Other banks via AA
    physical_assets: Decimal      # Property, gold, vehicle, etc.
    gross_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal

    # Drill-down
    breakdown: dict[str, Any] | None

    # History (optional, returned by /history endpoint)
    history: list["NetWorthHistoryPoint"] | None = None

    model_config = {"from_attributes": True}


class NetWorthHistoryPoint(BaseModel):
    """One data point in the net-worth time-series."""

    snapshot_id: uuid.UUID
    computed_at: datetime
    net_worth: Decimal
    gross_assets: Decimal
    total_liabilities: Decimal

    model_config = {"from_attributes": True}


class NetWorthRecomputeResponse(BaseModel):
    """Response after triggering a recompute."""

    message: str
    snapshot_id: uuid.UUID
    net_worth: Decimal
    computed_at: datetime
