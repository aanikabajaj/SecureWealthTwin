"""
SecureWealth Twin — Net Worth Snapshot Model.

Point-in-time record of a user's computed net worth across all asset classes.
Immutable once written; new snapshots are created on each recompute.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, Uuid, func
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class NetWorthSnapshot(Base):
    """
    Immutable net-worth snapshot computed by NetWorthService.

    Components
    ──────────
    financial_assets   : Savings + investments from primary bank
    aa_assets          : Balances fetched via Account Aggregator (other banks)
    physical_assets    : Property, gold, vehicles, etc. (user-declared)
    total_liabilities  : Outstanding loans across all sources
    net_worth          : financial_assets + aa_assets + physical_assets - total_liabilities

    Breakdown JSON stores category-level detail for drill-down UI.
    """

    __tablename__ = "networth_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Asset buckets (INR) ───────────────────────────────────────
    financial_assets: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=0, nullable=False
    )
    # Primary bank: savings + FD + investments from Transaction history

    aa_assets: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=0, nullable=False
    )
    # Balances from linked accounts via Account Aggregator

    physical_assets: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=0, nullable=False
    )
    # User-declared physical assets (effective value after ownership %)

    # ── Liabilities ───────────────────────────────────────────────
    total_liabilities: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=0, nullable=False
    )
    # Outstanding loans (home loan, vehicle loan, etc.)

    # ── Totals ────────────────────────────────────────────────────
    gross_assets: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=0, nullable=False
    )
    net_worth: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=0, nullable=False
    )

    # ── Drill-down breakdown ──────────────────────────────────────
    breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Example:
    # {
    #   "financial": {
    #       "savings": 250000, "investments": 180000, "fd": 100000
    #   },
    #   "aa": {
    #       "HDFC-FIP": 320000, "SBI-FIP": 95000
    #   },
    #   "physical": {
    #       "real_estate": 4500000, "gold": 350000, "vehicle": 450000
    #   },
    #   "liabilities": {
    #       "home_loan": 2200000, "vehicle_loan": 200000
    #   }
    # }

    # ── Timestamps ────────────────────────────────────────────────
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────
    user = relationship("User", back_populates="networth_snapshots")

    # ── Indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_networth_user_time", "user_id", "computed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<NetWorthSnapshot user={self.user_id} "
            f"net_worth={self.net_worth} at={self.computed_at}>"
        )
