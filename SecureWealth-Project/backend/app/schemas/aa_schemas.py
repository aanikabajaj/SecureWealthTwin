"""
SecureWealth Twin — Account Aggregator Pydantic Schemas.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from backend.app.models.aa_consent import AccountType, ConsentStatus, FetchStatus


class ConsentCreateRequest(BaseModel):
    aa_id: str = Field(..., description="AA identifier e.g. 'finvu' or 'onemoney'")
    purpose_code: str = Field("03", description="RBI purpose code")
    fi_types: list[str] = Field(
        default=["DEPOSIT", "MUTUAL_FUNDS", "EQUITIES"],
        description="Financial information types to request",
    )
    fetch_frequency: str = Field("MONTHLY", description="ONETIME | DAILY | WEEKLY | MONTHLY")
    consent_duration_days: int = Field(180, ge=1, le=730)
    date_range_months: int = Field(12, ge=1, le=24)

    @field_validator("aa_id")
    @classmethod
    def aa_id_must_be_known(cls, v: str) -> str:
        allowed = {"finvu", "onemoney", "anumati", "perfios", "cookiejar", "sandbox"}
        if v.lower() not in allowed:
            raise ValueError(f"Unknown AA. Supported: {allowed}")
        return v.lower()


class ConsentResponse(BaseModel):
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
    consent_handle: str
    consent_id: str | None = None
    status: ConsentStatus
    reason: str | None = None
    raw_payload: dict[str, Any] | None = None


class LinkedAccountResponse(BaseModel):
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
    current_balance: Decimal = Field(..., ge=0)


class FetchInitiateRequest(BaseModel):
    consent_id: uuid.UUID = Field(..., description="UUID of an ACTIVE consent")
    fi_types: list[str] | None = Field(None, description="Subset of FI types; None = all from consent")


class FetchStatusResponse(BaseModel):
    id: uuid.UUID
    session_id: str
    fi_type: str
    status: FetchStatus
    summary: dict[str, Any] | None
    fetch_error: str | None
    fetched_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FinancialPictureResponse(BaseModel):
    user_id: uuid.UUID
    total_aa_balance: Decimal
    accounts: list[LinkedAccountResponse]
    last_updated: datetime | None
    consent_count: int
    active_consent_count: int
