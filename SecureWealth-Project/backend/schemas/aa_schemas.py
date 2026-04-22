"""
SecureWealth Twin — Account Aggregator Pydantic Schemas.

Request / response models for all AA-related endpoints.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from backend.app.models.aa_consent import (
    AccountType,
    ConsentStatus,
    FetchStatus,
)


# ── Consent Schemas ───────────────────────────────────────────────────────────

class ConsentCreateRequest(BaseModel):
    """Body for POST /api/v1/aggregator/consents."""

    aa_id: str = Field(..., description="AA identifier, e.g. 'finvu' or 'onemoney'")
    purpose_code: str = Field("03", description="RBI purpose code")
    fi_types: list[str] = Field(
        default=["DEPOSIT", "MUTUAL_FUNDS", "EQUITIES"],
        description="Financial information types to request",
    )
    fetch_frequency: str = Field("MONTHLY", description="ONETIME | DAILY | WEEKLY | MONTHLY")
    consent_duration_days: int = Field(
        180, ge=1, le=730, description="How many days the consent should stay active"
    )
    date_range_months: int = Field(
        12, ge=1, le=24, description="How many months of historical data to request"
    )

    @field_validator("aa_id")
    @classmethod
    def aa_id_must_be_known(cls, v: str) -> str:
        allowed = {"finvu", "onemoney", "anumati", "perfios", "cookiejar", "sandbox"}
        if v.lower() not in allowed:
            raise ValueError(f"Unknown AA. Supported: {allowed}")
        return v.lower()


class ConsentResponse(BaseModel):
    """Response for a single consent artefact."""

    id: uuid.UUID
    aa_id: str
    consent_handle: str | None
    consent_id: str | None
    status: ConsentStatus
    fi_types: list[str] | None
    fetch_frequency: str
    consent_expiry: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConsentStatusUpdateRequest(BaseModel):
    """Webhook payload from the AA notifying consent status change."""

    consent_handle: str
    consent_id: str | None = None
    status: ConsentStatus
    reason: str | None = None
    raw_payload: dict[str, Any] | None = None


# ── Linked Account Schemas ────────────────────────────────────────────────────

class LinkedAccountResponse(BaseModel):
    """Response for a linked FIP account."""

    id: uuid.UUID
    fip_id: str
    fip_name: str
    account_type: AccountType
    masked_account_number: str | None
    ifsc: str | None
    current_balance: Decimal
    currency: str
    is_active: bool
    last_fetched_at: datetime | None

    model_config = {"from_attributes": True}


class LinkedAccountUpdateRequest(BaseModel):
    """Manually update a linked account's balance (e.g. after a fetch)."""

    current_balance: Decimal = Field(..., ge=0)


# ── Data Fetch Schemas ────────────────────────────────────────────────────────

class FetchInitiateRequest(BaseModel):
    """Body for POST /api/v1/aggregator/fetch — trigger data pull."""

    consent_id: uuid.UUID = Field(..., description="UUID of an ACTIVE consent")
    fi_types: list[str] | None = Field(
        None, description="Subset of FI types to fetch; None = all from consent"
    )


class FetchStatusResponse(BaseModel):
    """Response for a data-fetch session."""

    id: uuid.UUID
    session_id: str
    fi_type: str
    status: FetchStatus
    summary: dict[str, Any] | None
    fetch_error: str | None
    fetched_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Financial Picture ─────────────────────────────────────────────────────────

class FinancialPictureResponse(BaseModel):
    """
    Aggregated financial picture across all linked AA accounts.
    Returned by GET /api/v1/aggregator/financial-picture.
    """

    user_id: uuid.UUID
    total_aa_balance: Decimal
    accounts: list[LinkedAccountResponse]
    last_updated: datetime | None
    consent_count: int
    active_consent_count: int
