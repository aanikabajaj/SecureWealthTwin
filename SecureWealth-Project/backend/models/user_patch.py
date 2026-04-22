"""
SecureWealth Twin — User Model (UPDATED).

Add these relationships to the existing User class in backend/app/models/user.py.
The rest of the file stays exactly the same — only paste the relationships block.
"""

# ─────────────────────────────────────────────────────────────────────────────
# PATCH INSTRUCTIONS:
# In your existing backend/app/models/user.py, REPLACE the
# "── Relationships" block with the one below.
# ─────────────────────────────────────────────────────────────────────────────

# ── Relationships (loaded lazily by default) ─────────────────
# transactions = relationship(
#     "Transaction", back_populates="user", lazy="selectin"
# )
# wealth_profile = relationship(
#     "WealthProfile", back_populates="user", uselist=False, lazy="selectin"
# )

# ── ADD THESE NEW RELATIONSHIPS ──────────────────────────────
# aa_consents = relationship(
#     "AAConsent", back_populates="user", lazy="selectin"
# )
# aa_linked_accounts = relationship(
#     "AALinkedAccount", back_populates="user", lazy="selectin"
# )
# aa_fetched_data = relationship(
#     "AAFetchedData", back_populates="user", lazy="selectin"
# )
# physical_assets = relationship(
#     "PhysicalAsset", back_populates="user", lazy="selectin"
# )
# networth_snapshots = relationship(
#     "NetWorthSnapshot", back_populates="user", lazy="selectin"
# )

# ─────────────────────────────────────────────────────────────────────────────
# FULL UPDATED user.py below — copy this entire file to replace existing one:
# ─────────────────────────────────────────────────────────────────────────────

UPDATED_USER_MODEL = '''
"""
SecureWealth Twin — User Model.

Represents a platform user: customer, bank admin, or fraud analyst.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class UserRole(str, enum.Enum):
    """Roles that determine RBAC permissions."""

    CUSTOMER = "customer"
    BANK_ADMIN = "bank_admin"
    FRAUD_ANALYST = "fraud_analyst"


class User(Base):
    """Platform user account."""

    __tablename__ = "users"

    # ── Primary Key ──────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Identity ─────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Role & Access ────────────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        default=UserRole.CUSTOMER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── MFA ──────────────────────────────────────────────────────
    is_mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Timestamps ───────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    transactions = relationship(
        "Transaction", back_populates="user", lazy="selectin"
    )
    wealth_profile = relationship(
        "WealthProfile", back_populates="user", uselist=False, lazy="selectin"
    )
    aa_consents = relationship(
        "AAConsent", back_populates="user", lazy="selectin"
    )
    aa_linked_accounts = relationship(
        "AALinkedAccount", back_populates="user", lazy="selectin"
    )
    aa_fetched_data = relationship(
        "AAFetchedData", back_populates="user", lazy="selectin"
    )
    physical_assets = relationship(
        "PhysicalAsset", back_populates="user", lazy="selectin"
    )
    networth_snapshots = relationship(
        "NetWorthSnapshot", back_populates="user", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role.value}>"
'''
