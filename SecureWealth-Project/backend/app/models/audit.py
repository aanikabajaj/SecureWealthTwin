"""
SecureWealth Twin — AuditLog Model.
Immutable, hash-chained log of all important system events.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    action:      Mapped[str]           = mapped_column(String(128), nullable=False)
    resource:    Mapped[str | None]    = mapped_column(String(128), nullable=True)
    resource_id: Mapped[str | None]    = mapped_column(String(255), nullable=True)
    detail:      Mapped[dict | None]   = mapped_column(JSON, nullable=True)
    ip_address:  Mapped[str | None]    = mapped_column(String(45), nullable=True)
    user_agent:  Mapped[str | None]    = mapped_column(Text, nullable=True)
    prev_hash:   Mapped[str | None]    = mapped_column(String(64), nullable=True)
    # SHA-256 of previous log row — creates hash chain for tamper evidence

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} user={self.user_id}>"
