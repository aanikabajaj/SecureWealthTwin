"""
SecureWealth Twin — WealthProfile Model.
Stores aggregated financial metrics per user (primary bank / manual data).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class RiskTolerance(str, enum.Enum):
    CONSERVATIVE = "conservative"
    MODERATE     = "moderate"
    AGGRESSIVE   = "aggressive"


class WealthProfile(Base):
    __tablename__ = "wealth_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # ── Primary bank financial data ────────────────────────────────
    total_savings:     Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    total_investments: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    net_worth:         Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    monthly_income:    Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    monthly_expenses:  Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)

    risk_tolerance: Mapped[RiskTolerance] = mapped_column(
        Enum(RiskTolerance, name="risk_tolerance", native_enum=False),
        default=RiskTolerance.MODERATE,
        nullable=False,
    )

    investment_goals: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes:            Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="wealth_profile")

    def __repr__(self) -> str:
        return f"<WealthProfile user={self.user_id} net_worth={self.net_worth}>"
