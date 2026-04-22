"""
SecureWealth Twin — Account Aggregator (AA) Models.

Implements the RBI Account Aggregator framework:
  - AAConsent        : Consent artefact raised by the FIU (us) to the AA
  - AALinkedAccount  : Bank accounts discovered & linked via AA
  - AAFetchedData    : Raw financial information packets fetched from FIPs
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class ConsentStatus(str, enum.Enum):
    PENDING   = "pending"
    ACTIVE    = "active"
    PAUSED    = "paused"
    REVOKED   = "revoked"
    EXPIRED   = "expired"
    FAILED    = "failed"


class FetchStatus(str, enum.Enum):
    INITIATED   = "initiated"
    IN_PROGRESS = "in_progress"
    SUCCESS     = "success"
    PARTIAL     = "partial"
    FAILED      = "failed"


class AccountType(str, enum.Enum):
    SAVINGS       = "savings"
    CURRENT       = "current"
    RECURRING     = "recurring"
    FIXED_DEPOSIT = "fixed_deposit"
    MUTUAL_FUND   = "mutual_fund"
    EQUITY        = "equity"
    NPS           = "nps"
    INSURANCE     = "insurance"
    OTHER         = "other"


# ── Models ────────────────────────────────────────────────────────────────────

class AAConsent(Base):
    __tablename__ = "aa_consents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    aa_id: Mapped[str] = mapped_column(String(64), nullable=False)
    consent_handle: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    consent_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    purpose_code: Mapped[str] = mapped_column(String(32), nullable=False, default="03")
    fi_types: Mapped[list | None] = mapped_column(JSON, nullable=True)

    date_range_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    date_range_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consent_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetch_frequency: Mapped[str] = mapped_column(String(32), nullable=False, default="MONTHLY")

    status: Mapped[ConsentStatus] = mapped_column(
        Enum(ConsentStatus, name="consent_status", native_enum=False),
        default=ConsentStatus.PENDING, nullable=False, index=True,
    )
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user            = relationship("User", back_populates="aa_consents")
    linked_accounts = relationship("AALinkedAccount", back_populates="consent", cascade="all, delete-orphan")
    fetched_data    = relationship("AAFetchedData",   back_populates="consent", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_aa_consent_user_status", "user_id", "status"),)

    def __repr__(self) -> str:
        return f"<AAConsent {self.consent_handle} status={self.status}>"


class AALinkedAccount(Base):
    __tablename__ = "aa_linked_accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    consent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("aa_consents.id", ondelete="CASCADE"), nullable=False
    )

    fip_id: Mapped[str] = mapped_column(String(64), nullable=False)
    fip_name: Mapped[str] = mapped_column(String(128), nullable=False)
    account_ref_number: Mapped[str] = mapped_column(String(128), nullable=False)

    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, name="account_type", native_enum=False),
        nullable=False, default=AccountType.SAVINGS,
    )
    masked_account_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ifsc: Mapped[str | None] = mapped_column(String(11), nullable=True)

    current_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user    = relationship("User",      back_populates="aa_linked_accounts")
    consent = relationship("AAConsent", back_populates="linked_accounts")

    __table_args__ = (Index("ix_aa_linked_user_fip", "user_id", "fip_id"),)

    def __repr__(self) -> str:
        return f"<AALinkedAccount fip={self.fip_id} acc={self.masked_account_number}>"


class AAFetchedData(Base):
    __tablename__ = "aa_fetched_data"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    consent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("aa_consents.id", ondelete="CASCADE"), nullable=False
    )
    linked_account_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("aa_linked_accounts.id", ondelete="SET NULL"), nullable=True
    )

    session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    fi_type: Mapped[str] = mapped_column(String(32), nullable=False)

    status: Mapped[FetchStatus] = mapped_column(
        Enum(FetchStatus, name="fetch_status", native_enum=False),
        default=FetchStatus.INITIATED, nullable=False,
    )

    encrypted_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fetch_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user           = relationship("User",             back_populates="aa_fetched_data")
    consent        = relationship("AAConsent",        back_populates="fetched_data")
    linked_account = relationship("AALinkedAccount")

    __table_args__ = (
        Index("ix_aa_fetched_user_fi",  "user_id", "fi_type"),
        Index("ix_aa_fetched_session",  "session_id"),
    )

    def __repr__(self) -> str:
        return f"<AAFetchedData session={self.session_id} fi={self.fi_type} status={self.status}>"
