"""
SecureWealth Twin — Physical Asset Model.

Allows customers to register real-world assets (property, gold, vehicles,
jewellery, art, etc.) so they appear in the full net-worth computation.

All monetary values are stored in INR. For foreign-currency assets, the
caller converts before persisting (conversion rate is stored for reference).
"""

import enum
import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
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

class AssetCategory(str, enum.Enum):
    """Top-level category of the physical asset."""
    REAL_ESTATE     = "real_estate"     # Residential / commercial / land
    GOLD            = "gold"            # Physical gold / SGB / digital gold
    VEHICLE         = "vehicle"         # Car, bike, boat, aircraft
    JEWELLERY       = "jewellery"       # Diamond, silver, platinum
    ART_COLLECTIBLE = "art_collectible" # Paintings, watches, wine
    BUSINESS        = "business"        # Unlisted equity / partnership stake
    OTHER           = "other"


class ValuationMethod(str, enum.Enum):
    """How the asset value was determined."""
    SELF_DECLARED   = "self_declared"   # User's own estimate
    MARKET_PRICE    = "market_price"    # Live market price (e.g. gold MCX)
    GOVT_CIRCLE_RATE = "govt_circle_rate" # Property circle rate
    PROFESSIONAL    = "professional"    # Certified valuer report


class OwnershipType(str, enum.Enum):
    """Legal ownership structure."""
    SOLE            = "sole"
    JOINT           = "joint"
    INHERITED       = "inherited"
    TRUST           = "trust"


# ── Model ─────────────────────────────────────────────────────────────────────

class PhysicalAsset(Base):
    """
    A real-world asset registered by the customer for net-worth computation.

    Supports versioned valuations: when a user updates the value, the old
    row is NOT mutated — a new snapshot row can optionally be inserted and
    the `is_current` flag flipped. This gives a valuation history.
    """

    __tablename__ = "physical_assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Classification ────────────────────────────────────────────
    category: Mapped[AssetCategory] = mapped_column(
        Enum(AssetCategory, name="asset_category", native_enum=False),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # e.g. "2BHK Apartment Bandra", "22K Gold Coins 50g", "Honda City 2021"

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Valuation ─────────────────────────────────────────────────
    current_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    # INR value as of `valuation_date`

    purchase_value: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    valuation_date: Mapped[date] = mapped_column(Date, nullable=False)
    valuation_method: Mapped[ValuationMethod] = mapped_column(
        Enum(ValuationMethod, name="valuation_method", native_enum=False),
        default=ValuationMethod.SELF_DECLARED,
        nullable=False,
    )

    # ── Liabilities against the asset ─────────────────────────────
    outstanding_loan: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=0, nullable=False
    )
    # e.g. home loan outstanding; subtracted in net-worth calc

    # ── Ownership ─────────────────────────────────────────────────
    ownership_type: Mapped[OwnershipType] = mapped_column(
        Enum(OwnershipType, name="ownership_type", native_enum=False),
        default=OwnershipType.SOLE,
        nullable=False,
    )
    ownership_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("100.00"), nullable=False
    )
    # For joint ownership; net-worth uses (current_value * ownership_pct / 100)

    # ── Category-specific metadata ────────────────────────────────
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Flexible bag for category-specific fields:
    # real_estate : {"location": "Mumbai", "area_sqft": 850, "registration_no": "..."}
    # gold        : {"weight_grams": 50, "purity": "22K", "form": "coin"}
    # vehicle     : {"make": "Honda", "model": "City", "year": 2021, "reg_no": "MH01AB1234"}

    # ── Document proof ────────────────────────────────────────────
    document_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # S3 / blob URLs of sale deed, RC book, valuation report, etc.

    # ── Flags ─────────────────────────────────────────────────────
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # False when superseded by a newer valuation snapshot

    include_in_networth: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # User can exclude an asset (e.g. disputed property) from net-worth

    # ── Timestamps ────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────
    user = relationship("User", back_populates="physical_assets")

    # ── Indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_asset_user_category", "user_id", "category"),
        Index("ix_asset_user_current", "user_id", "is_current"),
    )

    # ── Computed helpers ──────────────────────────────────────────
    @property
    def effective_value(self) -> Decimal:
        """Net value after applying ownership percentage and outstanding loan."""
        owned = self.current_value * (self.ownership_percentage / Decimal("100"))
        return max(owned - self.outstanding_loan, Decimal("0"))

    @property
    def unrealised_gain(self) -> Decimal | None:
        """Simple gain over purchase price (not annualised)."""
        if self.purchase_value is None:
            return None
        return self.current_value - self.purchase_value

    def __repr__(self) -> str:
        return (
            f"<PhysicalAsset '{self.name}' category={self.category} "
            f"value={self.current_value}>"
        )
