"""
SecureWealth Twin — Model Registry.

Import all ORM models here so that:
  1. Alembic can discover them via `Base.metadata`
  2. Other modules can do: `from backend.app.models import User, Transaction, ...`
"""

# ── Existing models ───────────────────────────────────────────────────────────
from backend.app.models.user import User, UserRole
from backend.app.models.transaction import Transaction, TransactionType, TransactionStatus
from backend.app.models.audit import AuditLog
from backend.app.models.wealth_profile import WealthProfile, RiskTolerance

# ── New: Account Aggregator ───────────────────────────────────────────────────
from backend.app.models.aa_consent import (
    AAConsent,
    AALinkedAccount,
    AAFetchedData,
    ConsentStatus,
    FetchStatus,
    AccountType,
)

# ── New: Physical Assets ──────────────────────────────────────────────────────
from backend.app.models.physical_asset import (
    PhysicalAsset,
    AssetCategory,
    ValuationMethod,
    OwnershipType,
)

# ── New: Net Worth Snapshots ──────────────────────────────────────────────────
from backend.app.models.networth_snapshot import NetWorthSnapshot

__all__ = [
    # Users
    "User",
    "UserRole",
    # Transactions
    "Transaction",
    "TransactionType",
    "TransactionStatus",
    # Audit
    "AuditLog",
    # Wealth Profile
    "WealthProfile",
    "RiskTolerance",
    # Account Aggregator
    "AAConsent",
    "AALinkedAccount",
    "AAFetchedData",
    "ConsentStatus",
    "FetchStatus",
    "AccountType",
    # Physical Assets
    "PhysicalAsset",
    "AssetCategory",
    "ValuationMethod",
    "OwnershipType",
    # Net Worth
    "NetWorthSnapshot",
]
