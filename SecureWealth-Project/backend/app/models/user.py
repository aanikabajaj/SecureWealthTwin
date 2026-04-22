"""
SecureWealth Twin — User Model.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    ADVISOR  = "advisor"
    ADMIN    = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        default=UserRole.CUSTOMER,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    kyc_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    # pending | verified | rejected

    # Virtual User Address for Account Aggregator (e.g. user@finvu)
    aa_vua: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Security Metadata (Real-time tracking)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    active_devices_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # 2-Step Verification (OTP)
    otp_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    otp_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────
    wealth_profile   = relationship("WealthProfile", back_populates="user", uselist=False, lazy="selectin")
    transactions     = relationship("Transaction",   back_populates="user", lazy="selectin")
    audit_logs       = relationship("AuditLog",      back_populates="user", lazy="select")

    aa_consents        = relationship("AAConsent",       back_populates="user", lazy="selectin")
    aa_linked_accounts = relationship("AALinkedAccount", back_populates="user", lazy="selectin")
    aa_fetched_data    = relationship("AAFetchedData",   back_populates="user", lazy="selectin")
    physical_assets    = relationship("PhysicalAsset",   back_populates="user", lazy="selectin")
    networth_snapshots = relationship("NetWorthSnapshot",back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"
