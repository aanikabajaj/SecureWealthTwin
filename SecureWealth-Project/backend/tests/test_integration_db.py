"""
SecureWealth Twin — True DB Integration Tests.

Uses the in-memory SQLite engine from conftest.py.
Tests the full repository → service stack against a real DB (not mocks).

Run with:
    pytest backend/app/tests/test_integration_db.py -v --asyncio-mode=auto
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.aa_consent import AAConsent, ConsentStatus, AccountType
from backend.app.models.physical_asset import (
    AssetCategory, PhysicalAsset, ValuationMethod, OwnershipType
)
from backend.app.models.wealth_profile import WealthProfile, RiskTolerance
from backend.app.repositories.aa_repository import (
    AAConsentRepository, AALinkedAccountRepository, AAFetchedDataRepository
)
from backend.app.repositories.asset_repository import (
    PhysicalAssetRepository, NetWorthSnapshotRepository
)
from backend.app.schemas.aa_schemas import ConsentCreateRequest
from backend.app.schemas.asset_schemas import PhysicalAssetCreateRequest, PhysicalAssetUpdateRequest


# ── AA Consent Repository Integration ─────────────────────────────────────────

class TestAAConsentRepositoryIntegration:

    @pytest.mark.asyncio
    async def test_create_and_get_consent(self, db_session: AsyncSession, db_user):
        repo = AAConsentRepository(db_session)
        consent = AAConsent(
            id=uuid.uuid4(),
            user_id=db_user.id,
            aa_id="finvu",
            consent_handle=f"HDL-{uuid.uuid4().hex[:8]}",
            status=ConsentStatus.PENDING,
            purpose_code="03",
            fi_types=["DEPOSIT"],
            fetch_frequency="MONTHLY",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        created = await repo.create(consent)
        assert created.id is not None

        fetched = await repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.aa_id == "finvu"
        assert fetched.status == ConsentStatus.PENDING

    @pytest.mark.asyncio
    async def test_list_for_user_with_status_filter(self, db_session: AsyncSession, db_user):
        repo = AAConsentRepository(db_session)

        for status in [ConsentStatus.PENDING, ConsentStatus.ACTIVE, ConsentStatus.REVOKED]:
            consent = AAConsent(
                id=uuid.uuid4(),
                user_id=db_user.id,
                aa_id="finvu",
                consent_handle=f"HDL-{uuid.uuid4().hex[:8]}",
                status=status,
                purpose_code="03",
                fetch_frequency="MONTHLY",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            await repo.create(consent)

        active = await repo.list_for_user(db_user.id, status=ConsentStatus.ACTIVE)
        assert len(active) >= 1
        assert all(c.status == ConsentStatus.ACTIVE for c in active)

    @pytest.mark.asyncio
    async def test_update_status(self, db_session: AsyncSession, db_user):
        repo = AAConsentRepository(db_session)
        consent = AAConsent(
            id=uuid.uuid4(),
            user_id=db_user.id,
            aa_id="onemoney",
            consent_handle=f"HDL-{uuid.uuid4().hex[:8]}",
            status=ConsentStatus.PENDING,
            purpose_code="03",
            fetch_frequency="MONTHLY",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        created = await repo.create(consent)

        await repo.update_status(
            created.id,
            status=ConsentStatus.ACTIVE,
            consent_id_str="CNS-LIVE-001",
        )

        updated = await repo.get_by_id(created.id)
        assert updated.status == ConsentStatus.ACTIVE
        assert updated.consent_id == "CNS-LIVE-001"

    @pytest.mark.asyncio
    async def test_get_by_handle(self, db_session: AsyncSession, db_user):
        repo = AAConsentRepository(db_session)
        handle = f"HDL-UNIQUE-{uuid.uuid4().hex[:6]}"
        consent = AAConsent(
            id=uuid.uuid4(),
            user_id=db_user.id,
            aa_id="finvu",
            consent_handle=handle,
            status=ConsentStatus.PENDING,
            purpose_code="03",
            fetch_frequency="MONTHLY",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await repo.create(consent)

        found = await repo.get_by_handle(handle)
        assert found is not None
        assert found.consent_handle == handle

        not_found = await repo.get_by_handle("HDL-DOESNOTEXIST")
        assert not_found is None


# ── Physical Asset Repository Integration ──────────────────────────────────────

class TestPhysicalAssetRepositoryIntegration:

    @pytest_asyncio.fixture
    async def asset_repo(self, db_session):
        return PhysicalAssetRepository(db_session)

    @pytest.mark.asyncio
    async def test_create_and_retrieve_asset(self, asset_repo, db_user):
        asset = PhysicalAsset(
            id=uuid.uuid4(),
            user_id=db_user.id,
            category=AssetCategory.GOLD,
            name="22K Gold Coins 50g",
            current_value=Decimal("350000"),
            valuation_date=date(2024, 11, 1),
            valuation_method=ValuationMethod.MARKET_PRICE,
            outstanding_loan=Decimal("0"),
            ownership_percentage=Decimal("100"),
            is_current=True,
            include_in_networth=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        created = await asset_repo.create(asset)
        assert created.id is not None

        fetched = await asset_repo.get_by_id(created.id)
        assert fetched.name == "22K Gold Coins 50g"
        assert fetched.category == AssetCategory.GOLD

    @pytest.mark.asyncio
    async def test_list_for_user_current_only(self, asset_repo, db_user):
        # Create a current and a retired asset
        current = PhysicalAsset(
            id=uuid.uuid4(),
            user_id=db_user.id,
            category=AssetCategory.VEHICLE,
            name="Honda City 2021",
            current_value=Decimal("800000"),
            valuation_date=date.today(),
            outstanding_loan=Decimal("0"),
            ownership_percentage=Decimal("100"),
            is_current=True,
            include_in_networth=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        retired = PhysicalAsset(
            id=uuid.uuid4(),
            user_id=db_user.id,
            category=AssetCategory.VEHICLE,
            name="Old Bike 2015",
            current_value=Decimal("50000"),
            valuation_date=date(2020, 1, 1),
            outstanding_loan=Decimal("0"),
            ownership_percentage=Decimal("100"),
            is_current=False,   # retired
            include_in_networth=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await asset_repo.create(current)
        await asset_repo.create(retired)

        current_assets = await asset_repo.list_for_user(db_user.id, current_only=True)
        current_names = [a.name for a in current_assets]
        assert "Honda City 2021" in current_names
        assert "Old Bike 2015" not in current_names

    @pytest.mark.asyncio
    async def test_soft_retire(self, asset_repo, db_user):
        asset = PhysicalAsset(
            id=uuid.uuid4(),
            user_id=db_user.id,
            category=AssetCategory.JEWELLERY,
            name="Diamond Ring",
            current_value=Decimal("200000"),
            valuation_date=date.today(),
            outstanding_loan=Decimal("0"),
            ownership_percentage=Decimal("100"),
            is_current=True,
            include_in_networth=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        created = await asset_repo.create(asset)
        await asset_repo.soft_retire(created.id)

        fetched = await asset_repo.get_by_id(created.id)
        assert fetched.is_current is False

    @pytest.mark.asyncio
    async def test_total_effective_value(self, asset_repo, db_user):
        assets = [
            PhysicalAsset(
                id=uuid.uuid4(),
                user_id=db_user.id,
                category=AssetCategory.REAL_ESTATE,
                name=f"Property {i}",
                current_value=Decimal("1000000"),
                valuation_date=date.today(),
                outstanding_loan=Decimal("200000"),
                ownership_percentage=Decimal("100"),
                is_current=True,
                include_in_networth=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            for i in range(3)
        ]
        for a in assets:
            await asset_repo.create(a)

        total = await asset_repo.total_effective_value_for_user(db_user.id)
        # Each asset: effective = 1000000 - 200000 = 800000; 3 assets = 2400000
        assert total >= Decimal("2400000")

    @pytest.mark.asyncio
    async def test_category_summary(self, asset_repo, db_user):
        gold = PhysicalAsset(
            id=uuid.uuid4(),
            user_id=db_user.id,
            category=AssetCategory.GOLD,
            name="Gold Bar",
            current_value=Decimal("500000"),
            valuation_date=date.today(),
            outstanding_loan=Decimal("0"),
            ownership_percentage=Decimal("100"),
            is_current=True,
            include_in_networth=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await asset_repo.create(gold)

        summary = await asset_repo.summary_by_category(db_user.id)
        assert AssetCategory.GOLD in summary
        assert summary[AssetCategory.GOLD]["total_value"] >= Decimal("500000")


# ── Net Worth Snapshot Repository Integration ──────────────────────────────────

class TestNetWorthSnapshotRepositoryIntegration:

    @pytest.mark.asyncio
    async def test_create_and_get_latest(self, db_session: AsyncSession, db_user):
        from backend.app.models.networth_snapshot import NetWorthSnapshot
        repo = NetWorthSnapshotRepository(db_session)

        snap = NetWorthSnapshot(
            id=uuid.uuid4(),
            user_id=db_user.id,
            financial_assets=Decimal("430000"),
            aa_assets=Decimal("423500"),
            physical_assets=Decimal("8500000"),
            total_liabilities=Decimal("2200000"),
            gross_assets=Decimal("9353500"),
            net_worth=Decimal("7153500"),
            breakdown={"test": True},
            computed_at=datetime.now(timezone.utc),
        )
        await repo.create(snap)

        latest = await repo.latest_for_user(db_user.id)
        assert latest is not None
        assert latest.net_worth == Decimal("7153500")

    @pytest.mark.asyncio
    async def test_history_returns_most_recent_first(
        self, db_session: AsyncSession, db_user
    ):
        from backend.app.models.networth_snapshot import NetWorthSnapshot
        repo = NetWorthSnapshotRepository(db_session)

        for i, net_worth in enumerate([5000000, 6000000, 7000000]):
            snap = NetWorthSnapshot(
                id=uuid.uuid4(),
                user_id=db_user.id,
                financial_assets=Decimal("0"),
                aa_assets=Decimal("0"),
                physical_assets=Decimal(str(net_worth)),
                total_liabilities=Decimal("0"),
                gross_assets=Decimal(str(net_worth)),
                net_worth=Decimal(str(net_worth)),
                computed_at=datetime.now(timezone.utc) + timedelta(seconds=i),
            )
            await repo.create(snap)

        history = await repo.history_for_user(db_user.id, limit=3)
        assert history[0].net_worth >= history[-1].net_worth  # descending
