"""
SecureWealth Twin — Physical Asset Service & Net Worth Service.

PhysicalAssetService  : CRUD + valuation history for real-world assets.
NetWorthService       : Recomputes and snapshots a user's full net worth
                        across all asset classes (primary bank + AA + physical).
"""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.networth_snapshot import NetWorthSnapshot
from backend.app.models.physical_asset import PhysicalAsset
from backend.app.models.wealth_profile import WealthProfile
from backend.app.repositories.aa_repository import AALinkedAccountRepository
from backend.app.repositories.asset_repository import (
    NetWorthSnapshotRepository,
    PhysicalAssetRepository,
)
from backend.app.schemas.asset_schemas import (
    AssetSummaryByCategory,
    NetWorthRecomputeResponse,
    NetWorthResponse,
    PhysicalAssetCreateRequest,
    PhysicalAssetResponse,
    PhysicalAssetUpdateRequest,
)

logger = logging.getLogger(__name__)


# ── Physical Asset Service ────────────────────────────────────────────────────

class PhysicalAssetService:
    """
    Manages the full lifecycle of a user's physical / real-world assets.

    Design decision: updates create a NEW row with is_current=True and retire
    the old row (is_current=False). This gives a free valuation history
    without a separate history table.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PhysicalAssetRepository(db)

    async def add_asset(
        self, user_id: uuid.UUID, req: PhysicalAssetCreateRequest
    ) -> PhysicalAssetResponse:
        asset = PhysicalAsset(
            user_id=user_id,
            category=req.category,
            name=req.name,
            description=req.description,
            current_value=req.current_value,
            purchase_value=req.purchase_value,
            purchase_date=req.purchase_date,
            valuation_date=req.valuation_date,
            valuation_method=req.valuation_method,
            outstanding_loan=req.outstanding_loan,
            ownership_type=req.ownership_type,
            ownership_percentage=req.ownership_percentage,
            metadata_json=req.metadata_json,
            document_urls=req.document_urls,
            include_in_networth=req.include_in_networth,
            is_current=True,
        )
        created = await self.repo.create(asset)
        logger.info("Asset added: user=%s category=%s value=%s", user_id, req.category, req.current_value)
        return self._to_response(created)

    async def update_asset(
        self,
        user_id: uuid.UUID,
        asset_id: uuid.UUID,
        req: PhysicalAssetUpdateRequest,
    ) -> PhysicalAssetResponse:
        """
        Retire the old record and create a new snapshot with updated values.
        Preserves full valuation history.
        """
        existing = await self.repo.get_user_asset(user_id, asset_id)
        if not existing:
            raise ValueError(f"Asset {asset_id} not found for user {user_id}")

        # Retire old record
        await self.repo.soft_retire(asset_id)

        # Clone with updates
        update_data = req.model_dump(exclude_none=True)
        new_asset = PhysicalAsset(
            user_id=user_id,
            category=existing.category,
            name=update_data.get("name", existing.name),
            description=update_data.get("description", existing.description),
            current_value=update_data.get("current_value", existing.current_value),
            purchase_value=existing.purchase_value,
            purchase_date=existing.purchase_date,
            valuation_date=update_data.get("valuation_date", existing.valuation_date),
            valuation_method=update_data.get("valuation_method", existing.valuation_method),
            outstanding_loan=update_data.get("outstanding_loan", existing.outstanding_loan),
            ownership_type=existing.ownership_type,
            ownership_percentage=update_data.get("ownership_percentage", existing.ownership_percentage),
            metadata_json=update_data.get("metadata_json", existing.metadata_json),
            document_urls=update_data.get("document_urls", existing.document_urls),
            include_in_networth=update_data.get("include_in_networth", existing.include_in_networth),
            is_current=True,
        )
        created = await self.repo.create(new_asset)
        return self._to_response(created)

    async def delete_asset(self, user_id: uuid.UUID, asset_id: uuid.UUID) -> None:
        existing = await self.repo.get_user_asset(user_id, asset_id)
        if not existing:
            raise ValueError(f"Asset {asset_id} not found")
        await self.repo.soft_retire(asset_id)

    async def list_assets(
        self,
        user_id: uuid.UUID,
        category: str | None = None,
    ) -> list[PhysicalAssetResponse]:
        from backend.app.models.physical_asset import AssetCategory
        cat = AssetCategory(category) if category else None
        assets = await self.repo.list_for_user(user_id, current_only=True, category=cat)
        return [self._to_response(a) for a in assets]

    async def get_asset(
        self, user_id: uuid.UUID, asset_id: uuid.UUID
    ) -> PhysicalAssetResponse:
        asset = await self.repo.get_user_asset(user_id, asset_id)
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        return self._to_response(asset)

    async def category_summary(
        self, user_id: uuid.UUID
    ) -> list[AssetSummaryByCategory]:
        breakdown = await self.repo.summary_by_category(user_id)
        return [
            AssetSummaryByCategory(
                category=cat,
                total_value=data["total_value"],
                total_effective_value=data["total_effective_value"],
                total_outstanding_loan=data["total_outstanding_loan"],
                count=data["count"],
            )
            for cat, data in breakdown.items()
        ]

    # ── Internal helpers ───────────────────────────────────────────

    @staticmethod
    def _to_response(asset: PhysicalAsset) -> PhysicalAssetResponse:
        return PhysicalAssetResponse(
            id=asset.id,
            user_id=asset.user_id,
            category=asset.category,
            name=asset.name,
            description=asset.description,
            current_value=asset.current_value,
            purchase_value=asset.purchase_value,
            purchase_date=asset.purchase_date,
            valuation_date=asset.valuation_date,
            valuation_method=asset.valuation_method,
            outstanding_loan=asset.outstanding_loan,
            ownership_type=asset.ownership_type,
            ownership_percentage=asset.ownership_percentage,
            effective_value=asset.effective_value,
            unrealised_gain=asset.unrealised_gain,
            metadata_json=asset.metadata_json,
            document_urls=asset.document_urls,
            include_in_networth=asset.include_in_networth,
            is_current=asset.is_current,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )


# ── Net Worth Service ─────────────────────────────────────────────────────────

class NetWorthService:
    """
    Computes and snapshots a user's complete net worth.

    Formula
    ───────
    gross_assets      = financial_assets + aa_assets + physical_assets
    total_liabilities = outstanding loans on physical assets
                        (AA/bank liabilities can be added later)
    net_worth         = gross_assets - total_liabilities

    financial_assets come from WealthProfile (kept by existing WealthTwinService).
    aa_assets come from AALinkedAccount.current_balance sum.
    physical_assets come from PhysicalAsset.effective_value sum.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.snapshot_repo = NetWorthSnapshotRepository(db)
        self.asset_repo    = PhysicalAssetRepository(db)
        self.aa_repo       = AALinkedAccountRepository(db)

    async def recompute(self, user_id: uuid.UUID) -> NetWorthRecomputeResponse:
        """
        Run a full recompute, persist a new snapshot, and return the result.
        Safe to call multiple times — each call creates one immutable snapshot row.
        """
        # 1. Financial assets from WealthProfile (primary bank)
        financial_assets = await self._get_financial_assets(user_id)

        # 2. AA assets (sum of all active linked-account balances)
        aa_balance = await self.aa_repo.total_balance_for_user(user_id)
        aa_assets = Decimal(str(aa_balance))

        # 3. Physical assets (ownership-adjusted, loan-deducted effective value)
        physical_effective = await self.asset_repo.total_effective_value_for_user(user_id)
        physical_liabilities = await self.asset_repo.total_liabilities_for_user(user_id)

        # 4. Build breakdown JSON
        category_data = await self.asset_repo.summary_by_category(user_id)
        breakdown = {
            "financial": {
                "primary_bank_assets": float(financial_assets),
            },
            "aa": {
                "total_linked_accounts": float(aa_assets),
            },
            "physical": {
                cat.value: {
                    "total_value": float(data["total_value"]),
                    "effective_value": float(data["total_effective_value"]),
                    "outstanding_loan": float(data["total_outstanding_loan"]),
                    "count": data["count"],
                }
                for cat, data in category_data.items()
            },
            "liabilities": {
                "physical_asset_loans": float(physical_liabilities),
            },
        }

        # 5. Totals
        gross_assets      = financial_assets + aa_assets + physical_effective + physical_liabilities
        # (physical_effective already deducted loans; add them back for gross, subtract for net)
        gross_assets      = financial_assets + aa_assets + (physical_effective + physical_liabilities)
        total_liabilities = physical_liabilities
        net_worth         = gross_assets - total_liabilities

        # 6. Persist snapshot
        snapshot = NetWorthSnapshot(
            user_id=user_id,
            financial_assets=financial_assets,
            aa_assets=aa_assets,
            physical_assets=physical_effective + physical_liabilities,  # gross physical
            total_liabilities=total_liabilities,
            gross_assets=gross_assets,
            net_worth=net_worth,
            breakdown=breakdown,
        )
        saved = await self.snapshot_repo.create(snapshot)

        # 7. Also update the existing WealthProfile.net_worth for backwards compat
        await self._sync_wealth_profile(user_id, net_worth)

        logger.info(
            "NetWorth recomputed: user=%s net_worth=%s", user_id, net_worth
        )

        return NetWorthRecomputeResponse(
            message="Net worth recomputed successfully",
            snapshot_id=saved.id,
            net_worth=net_worth,
            computed_at=saved.computed_at,
        )

    async def get_latest(self, user_id: uuid.UUID) -> NetWorthResponse | None:
        snapshot = await self.snapshot_repo.latest_for_user(user_id)
        if not snapshot:
            return None
        return NetWorthResponse(
            user_id=user_id,
            snapshot_id=snapshot.id,
            computed_at=snapshot.computed_at,
            financial_assets=snapshot.financial_assets,
            aa_assets=snapshot.aa_assets,
            physical_assets=snapshot.physical_assets,
            gross_assets=snapshot.gross_assets,
            total_liabilities=snapshot.total_liabilities,
            net_worth=snapshot.net_worth,
            breakdown=snapshot.breakdown,
        )

    async def get_history(
        self, user_id: uuid.UUID, limit: int = 12
    ) -> list[NetWorthResponse]:
        snapshots = await self.snapshot_repo.history_for_user(user_id, limit=limit)
        return [
            NetWorthResponse(
                user_id=user_id,
                snapshot_id=s.id,
                computed_at=s.computed_at,
                financial_assets=s.financial_assets,
                aa_assets=s.aa_assets,
                physical_assets=s.physical_assets,
                gross_assets=s.gross_assets,
                total_liabilities=s.total_liabilities,
                net_worth=s.net_worth,
                breakdown=s.breakdown,
            )
            for s in snapshots
        ]

    # ── Internal helpers ───────────────────────────────────────────

    async def _get_financial_assets(self, user_id: uuid.UUID) -> Decimal:
        """Pull savings + investments from WealthProfile (primary bank data)."""
        from sqlalchemy import select
        stmt = select(WealthProfile).where(WealthProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            return Decimal("0")
        return (profile.total_savings or Decimal("0")) + (profile.total_investments or Decimal("0"))

    async def _sync_wealth_profile(
        self, user_id: uuid.UUID, net_worth: Decimal
    ) -> None:
        """Keep WealthProfile.net_worth in sync with the new snapshot."""
        from sqlalchemy import update
        stmt = (
            update(WealthProfile)
            .where(WealthProfile.user_id == user_id)
            .values(net_worth=net_worth)
        )
        await self.db.execute(stmt)
        await self.db.flush()
