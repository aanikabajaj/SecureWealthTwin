"""
SecureWealth Twin — Physical Asset & Net Worth Repository.
"""

import uuid
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.repository_base import BaseRepository
from backend.app.models.physical_asset import AssetCategory, PhysicalAsset
from backend.app.models.networth_snapshot import NetWorthSnapshot


class PhysicalAssetRepository(BaseRepository[PhysicalAsset]):
    model = PhysicalAsset

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        current_only: bool = True,
        include_in_networth: bool | None = None,
        category: AssetCategory | None = None,
    ) -> list[PhysicalAsset]:
        stmt = select(PhysicalAsset).where(PhysicalAsset.user_id == user_id)
        if current_only:
            stmt = stmt.where(PhysicalAsset.is_current == True)  # noqa: E712
        if include_in_networth is not None:
            stmt = stmt.where(PhysicalAsset.include_in_networth == include_in_networth)
        if category:
            stmt = stmt.where(PhysicalAsset.category == category)
        stmt = stmt.order_by(PhysicalAsset.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_asset(
        self, user_id: uuid.UUID, asset_id: uuid.UUID
    ) -> PhysicalAsset | None:
        """Fetch asset only if it belongs to the user."""
        stmt = (
            select(PhysicalAsset)
            .where(PhysicalAsset.id == asset_id)
            .where(PhysicalAsset.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def soft_retire(self, asset_id: uuid.UUID) -> None:
        """Mark asset as non-current (historical snapshot)."""
        stmt = (
            update(PhysicalAsset)
            .where(PhysicalAsset.id == asset_id)
            .values(is_current=False)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def total_effective_value_for_user(self, user_id: uuid.UUID) -> Decimal:
        """
        Sum of effective_value (ownership-adjusted, loan-deducted) for all
        current assets flagged include_in_networth=True.
        """
        assets = await self.list_for_user(
            user_id, current_only=True, include_in_networth=True
        )
        return sum((a.effective_value for a in assets), Decimal("0"))

    async def total_liabilities_for_user(self, user_id: uuid.UUID) -> Decimal:
        """Sum of outstanding_loan across all current assets."""
        assets = await self.list_for_user(user_id, current_only=True)
        return sum((a.outstanding_loan for a in assets), Decimal("0"))

    async def summary_by_category(
        self, user_id: uuid.UUID
    ) -> dict[AssetCategory, dict]:
        """Returns per-category totals for the breakdown JSON."""
        assets = await self.list_for_user(
            user_id, current_only=True, include_in_networth=True
        )
        result: dict[AssetCategory, dict] = {}
        for a in assets:
            cat = a.category
            if cat not in result:
                result[cat] = {
                    "total_value": Decimal("0"),
                    "total_effective_value": Decimal("0"),
                    "total_outstanding_loan": Decimal("0"),
                    "count": 0,
                }
            result[cat]["total_value"] += a.current_value
            result[cat]["total_effective_value"] += a.effective_value
            result[cat]["total_outstanding_loan"] += a.outstanding_loan
            result[cat]["count"] += 1
        return result


class NetWorthSnapshotRepository(BaseRepository[NetWorthSnapshot]):
    model = NetWorthSnapshot

    async def latest_for_user(self, user_id: uuid.UUID) -> NetWorthSnapshot | None:
        stmt = (
            select(NetWorthSnapshot)
            .where(NetWorthSnapshot.user_id == user_id)
            .order_by(NetWorthSnapshot.computed_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def history_for_user(
        self,
        user_id: uuid.UUID,
        limit: int = 12,
    ) -> list[NetWorthSnapshot]:
        stmt = (
            select(NetWorthSnapshot)
            .where(NetWorthSnapshot.user_id == user_id)
            .order_by(NetWorthSnapshot.computed_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
