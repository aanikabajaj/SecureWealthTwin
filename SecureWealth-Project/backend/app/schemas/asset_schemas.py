"""
SecureWealth Twin — Physical Asset & Net Worth Pydantic Schemas.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.models.physical_asset import AssetCategory, OwnershipType, ValuationMethod


class PhysicalAssetCreateRequest(BaseModel):
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
    ownership_percentage: Decimal = Field(default=Decimal("100.00"), gt=0, le=Decimal("100.00"))

    metadata_json: dict[str, Any] | None = None
    document_urls: list[str] | None = None
    include_in_networth: bool = True

    @model_validator(mode="after")
    def validate_purchase_date(self) -> "PhysicalAssetCreateRequest":
        if self.purchase_date and self.purchase_date > self.valuation_date:
            raise ValueError("purchase_date cannot be after valuation_date")
        return self


class PhysicalAssetUpdateRequest(BaseModel):
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
    effective_value: Decimal
    unrealised_gain: Decimal | None
    metadata_json: dict[str, Any] | None
    document_urls: list[str] | None
    include_in_networth: bool
    is_current: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetSummaryByCategory(BaseModel):
    category: AssetCategory
    total_value: Decimal
    total_effective_value: Decimal
    total_outstanding_loan: Decimal
    count: int


class NetWorthResponse(BaseModel):
    user_id: uuid.UUID
    snapshot_id: uuid.UUID
    computed_at: datetime
    financial_assets: Decimal
    aa_assets: Decimal
    physical_assets: Decimal
    gross_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    breakdown: dict[str, Any] | None
    history: list["NetWorthHistoryPoint"] | None = None

    model_config = {"from_attributes": True}


class NetWorthHistoryPoint(BaseModel):
    snapshot_id: uuid.UUID
    computed_at: datetime
    net_worth: Decimal
    gross_assets: Decimal
    total_liabilities: Decimal

    model_config = {"from_attributes": True}


class NetWorthRecomputeResponse(BaseModel):
    message: str
    snapshot_id: uuid.UUID
    net_worth: Decimal
    computed_at: datetime
