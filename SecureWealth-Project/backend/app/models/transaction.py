"""
SecureWealth Twin — Transaction Model.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class TransactionType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT  = "debit"


class TransactionStatus(str, enum.Enum):
    PENDING   = "pending"
    COMPLETED = "completed"
    FAILED    = "failed"
    REVERSED  = "reversed"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    amount:      Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency:    Mapped[str]     = mapped_column(String(3), default="INR", nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category:    Mapped[str | None] = mapped_column(String(64), nullable=True)
    reference:   Mapped[str | None] = mapped_column(String(128), nullable=True)

    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type", native_enum=False),
        nullable=False,
    )
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status", native_enum=False),
        default=TransactionStatus.COMPLETED,
        nullable=False,
    )

    transacted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at:    Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.transaction_type} {self.amount} {self.status}>"
