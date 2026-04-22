"""
SecureWealth Twin — Net Worth Snapshot Model.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, Uuid, func
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class NetWorthSnapshot(Base):
    __tablename__ = "networth_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    financial_assets:  Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    aa_assets:         Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    physical_assets:   Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    gross_assets:      Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    net_worth:         Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)

    breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="networth_snapshots")

    __table_args__ = (Index("ix_networth_user_time", "user_id", "computed_at"),)

    def __repr__(self) -> str:
        return f"<NetWorthSnapshot user={self.user_id} net_worth={self.net_worth} at={self.computed_at}>"
