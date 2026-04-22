"""
SecureWealth Twin — Model Registry.
"""

from backend.app.models.user import User, UserRole
from backend.app.models.transaction import Transaction, TransactionType, TransactionStatus
from backend.app.models.audit import AuditLog
from backend.app.models.wealth_profile import WealthProfile, RiskTolerance

from backend.app.models.aa_consent import (
    AAConsent, AALinkedAccount, AAFetchedData,
    ConsentStatus, FetchStatus, AccountType,
)
from backend.app.models.physical_asset import (
    PhysicalAsset, AssetCategory, ValuationMethod, OwnershipType,
)
from backend.app.models.networth_snapshot import NetWorthSnapshot

__all__ = [
    "User", "UserRole",
    "Transaction", "TransactionType", "TransactionStatus",
    "AuditLog",
    "WealthProfile", "RiskTolerance",
    "AAConsent", "AALinkedAccount", "AAFetchedData",
    "ConsentStatus", "FetchStatus", "AccountType",
    "PhysicalAsset", "AssetCategory", "ValuationMethod", "OwnershipType",
    "NetWorthSnapshot",
]
