"""
SecureWealth Twin — Physical Asset Model.
"""

import enum
import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, ForeignKey, Index,
    Numeric, String, Text, Uuid, func,
)
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class AssetCategory(str, enum.Enum):
    REAL_ESTATE     = "real_estate"
    GOLD            = "gold"
    VEHICLE         = "vehicle"
    JEWELLERY       = "jewellery"
    ART_COLLECTIBLE = "art_collectible"
    BUSINESS        = "business"
    OTHER           = "other"


class ValuationMethod(str, enum.Enum):
    SELF_DECLARED    = "self_declared"
    MARKET_PRICE     = "market_price"
    GOVT_CIRCLE_RATE = "govt_circle_rate"
    PROFESSIONAL     = "professional"


class OwnershipType(str, enum.Enum):
    SOLE      = "sole"
    JOINT     = "joint"
    INHERITED = "inherited"
    TRUST     = "trust"


class PhysicalAsset(Base):
    __tablename__ = "physical_assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    category: Mapped[AssetCategory] = mapped_column(
        Enum(AssetCategory, name="asset_category", native_enum=False),
        nullable=False, index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    current_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    purchase_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    valuation_date: Mapped[date] = mapped_column(Date, nullable=False)
    valuation_method: Mapped[ValuationMethod] = mapped_column(
        Enum(ValuationMethod, name="valuation_method", native_enum=False),
        default=ValuationMethod.SELF_DECLARED, nullable=False,
    )

    outstanding_loan: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)

    ownership_type: Mapped[OwnershipType] = mapped_column(
        Enum(OwnershipType, name="ownership_type", native_enum=False),
        default=OwnershipType.SOLE, nullable=False,
    )
    ownership_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("100.00"), nullable=False
    )

    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    document_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)

    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_in_networth: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="physical_assets")

    __table_args__ = (
        Index("ix_asset_user_category", "user_id", "category"),
        Index("ix_asset_user_current",  "user_id", "is_current"),
    )

    @property
    def effective_value(self) -> Decimal:
        owned = self.current_value * (self.ownership_percentage / Decimal("100"))
        return max(owned - self.outstanding_loan, Decimal("0"))

    @property
    def unrealised_gain(self) -> Decimal | None:
        if self.purchase_value is None:
            return None
        return self.current_value - self.purchase_value

    def __repr__(self) -> str:
        return f"<PhysicalAsset '{self.name}' category={self.category} value={self.current_value}>"
