"""
SecureWealth Twin — Model Registry.
"""

from app.models.user import User, UserRole
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.audit import AuditLog
from app.models.wealth_profile import WealthProfile, RiskTolerance

from app.models.aa_consent import (
    AAConsent, AALinkedAccount, AAFetchedData,
    ConsentStatus, FetchStatus, AccountType,
)
from app.models.physical_asset import (
    PhysicalAsset, AssetCategory, ValuationMethod, OwnershipType,
)
from app.models.networth_snapshot import NetWorthSnapshot

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
