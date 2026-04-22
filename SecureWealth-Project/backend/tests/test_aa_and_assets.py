"""
SecureWealth Twin — Tests: Account Aggregator & Physical Assets.

Run with:
    pytest backend/app/tests/test_aa_and_assets.py -v --asyncio-mode=auto
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.aa_consent import (
    AAConsent,
    AAFetchedData,
    AALinkedAccount,
    AccountType,
    ConsentStatus,
    FetchStatus,
)
from backend.app.models.physical_asset import (
    AssetCategory,
    OwnershipType,
    PhysicalAsset,
    ValuationMethod,
)
from backend.app.models.networth_snapshot import NetWorthSnapshot
from backend.app.schemas.aa_schemas import ConsentCreateRequest, FetchInitiateRequest
from backend.app.schemas.asset_schemas import (
    PhysicalAssetCreateRequest,
    PhysicalAssetUpdateRequest,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_db():
    """Minimal AsyncSession mock."""
    db = AsyncMock(spec=AsyncSession)
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def sample_consent(user_id) -> AAConsent:
    return AAConsent(
        id=uuid.uuid4(),
        user_id=user_id,
        aa_id="finvu",
        consent_handle="HDL-TEST123",
        consent_id="CNS-ABC456",
        status=ConsentStatus.ACTIVE,
        purpose_code="03",
        fi_types=["DEPOSIT", "MUTUAL_FUNDS"],
        fetch_frequency="MONTHLY",
        consent_expiry=datetime.now(timezone.utc) + timedelta(days=180),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_linked_account(user_id, sample_consent) -> AALinkedAccount:
    return AALinkedAccount(
        id=uuid.uuid4(),
        user_id=user_id,
        consent_id=sample_consent.id,
        fip_id="HDFC-FIP",
        fip_name="HDFC",
        account_ref_number="REF001",
        account_type=AccountType.SAVINGS,
        masked_account_number="XXXX4521",
        ifsc="HDFC0001234",
        current_balance=Decimal("325000.00"),
        currency="INR",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_physical_asset(user_id) -> PhysicalAsset:
    return PhysicalAsset(
        id=uuid.uuid4(),
        user_id=user_id,
        category=AssetCategory.REAL_ESTATE,
        name="2BHK Apartment Bandra",
        current_value=Decimal("8500000.00"),
        purchase_value=Decimal("5000000.00"),
        purchase_date=date(2018, 3, 15),
        valuation_date=date(2024, 11, 1),
        valuation_method=ValuationMethod.GOVT_CIRCLE_RATE,
        outstanding_loan=Decimal("2200000.00"),
        ownership_type=OwnershipType.SOLE,
        ownership_percentage=Decimal("100.00"),
        include_in_networth=True,
        is_current=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ── PhysicalAsset model tests ─────────────────────────────────────────────────

class TestPhysicalAssetModel:

    def test_effective_value_sole_ownership(self, sample_physical_asset):
        """Sole owner: effective = current_value - outstanding_loan."""
        assert sample_physical_asset.effective_value == Decimal("6300000.00")

    def test_effective_value_joint_ownership(self, sample_physical_asset):
        """50% owner: effective = (8500000 * 0.5) - 2200000 = 2050000."""
        sample_physical_asset.ownership_percentage = Decimal("50.00")
        assert sample_physical_asset.effective_value == Decimal("2050000.00")

    def test_effective_value_never_negative(self, sample_physical_asset):
        """Loan > value should return 0, not negative."""
        sample_physical_asset.outstanding_loan = Decimal("99999999.00")
        assert sample_physical_asset.effective_value == Decimal("0")

    def test_unrealised_gain(self, sample_physical_asset):
        """Gain = current - purchase."""
        assert sample_physical_asset.unrealised_gain == Decimal("3500000.00")

    def test_unrealised_gain_none_when_no_purchase(self, sample_physical_asset):
        sample_physical_asset.purchase_value = None
        assert sample_physical_asset.unrealised_gain is None

    def test_gold_asset_repr(self, user_id):
        asset = PhysicalAsset(
            id=uuid.uuid4(),
            user_id=user_id,
            category=AssetCategory.GOLD,
            name="22K Gold Coins 50g",
            current_value=Decimal("350000"),
            valuation_date=date.today(),
            outstanding_loan=Decimal("0"),
            ownership_percentage=Decimal("100"),
            is_current=True,
        )
        assert "GOLD" in repr(asset).upper() or "gold" in repr(asset)


# ── ConsentCreateRequest schema tests ─────────────────────────────────────────

class TestConsentCreateSchema:

    def test_valid_request(self):
        req = ConsentCreateRequest(
            aa_id="finvu",
            purpose_code="03",
            fi_types=["DEPOSIT"],
            fetch_frequency="MONTHLY",
            consent_duration_days=180,
            date_range_months=12,
        )
        assert req.aa_id == "finvu"

    def test_unknown_aa_id_raises(self):
        with pytest.raises(Exception):
            ConsentCreateRequest(aa_id="unknown_bank_xyz")

    def test_aa_id_normalised_to_lowercase(self):
        req = ConsentCreateRequest(aa_id="FINVU")
        assert req.aa_id == "finvu"

    def test_duration_bounds(self):
        with pytest.raises(Exception):
            ConsentCreateRequest(aa_id="finvu", consent_duration_days=0)
        with pytest.raises(Exception):
            ConsentCreateRequest(aa_id="finvu", consent_duration_days=1000)


# ── PhysicalAssetCreateRequest schema tests ───────────────────────────────────

class TestPhysicalAssetCreateSchema:

    def test_valid_real_estate(self):
        req = PhysicalAssetCreateRequest(
            category=AssetCategory.REAL_ESTATE,
            name="Flat in Pune",
            current_value=Decimal("4500000"),
            valuation_date=date.today(),
            valuation_method=ValuationMethod.SELF_DECLARED,
        )
        assert req.outstanding_loan == Decimal("0")
        assert req.ownership_percentage == Decimal("100.00")

    def test_purchase_date_after_valuation_raises(self):
        with pytest.raises(Exception):
            PhysicalAssetCreateRequest(
                category=AssetCategory.GOLD,
                name="Gold",
                current_value=Decimal("100000"),
                valuation_date=date(2023, 1, 1),
                purchase_date=date(2024, 1, 1),  # after valuation_date
            )

    def test_ownership_percentage_bounds(self):
        with pytest.raises(Exception):
            PhysicalAssetCreateRequest(
                category=AssetCategory.VEHICLE,
                name="Car",
                current_value=Decimal("800000"),
                valuation_date=date.today(),
                ownership_percentage=Decimal("0"),
            )
        with pytest.raises(Exception):
            PhysicalAssetCreateRequest(
                category=AssetCategory.VEHICLE,
                name="Car",
                current_value=Decimal("800000"),
                valuation_date=date.today(),
                ownership_percentage=Decimal("101"),
            )

    def test_zero_current_value_raises(self):
        with pytest.raises(Exception):
            PhysicalAssetCreateRequest(
                category=AssetCategory.GOLD,
                name="Gold",
                current_value=Decimal("0"),
                valuation_date=date.today(),
            )


# ── AccountAggregatorService tests ────────────────────────────────────────────

class TestAccountAggregatorService:

    @pytest.mark.asyncio
    async def test_create_consent_sandbox(self, user_id, mock_db):
        """In sandbox mode, consent is created with PENDING status."""
        from backend.app.services.aa_service import AccountAggregatorService

        req = ConsentCreateRequest(
            aa_id="finvu",
            fi_types=["DEPOSIT"],
            consent_duration_days=180,
            date_range_months=12,
        )

        created_consent = AAConsent(
            id=uuid.uuid4(),
            user_id=user_id,
            aa_id="finvu",
            consent_handle="HDL-SANDBOX",
            status=ConsentStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        with patch(
            "backend.app.services.aa_service.AAConsentRepository"
        ) as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.create.return_value = created_consent
            MockRepo.return_value = mock_repo

            with patch(
                "backend.app.services.aa_service.AALinkedAccountRepository"
            ):
                with patch(
                    "backend.app.services.aa_service.AAFetchedDataRepository"
                ):
                    svc = AccountAggregatorService(mock_db)
                    result = await svc.create_consent(user_id, req)

        assert result.status == ConsentStatus.PENDING
        assert result.aa_id == "finvu"
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_initiate_fetch_requires_active_consent(self, user_id, mock_db, sample_consent):
        """Fetch should raise ValueError if consent is not ACTIVE."""
        from backend.app.services.aa_service import AccountAggregatorService

        sample_consent.status = ConsentStatus.PENDING  # not active

        with patch(
            "backend.app.services.aa_service.AAConsentRepository"
        ) as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = sample_consent
            MockRepo.return_value = mock_repo

            with patch("backend.app.services.aa_service.AALinkedAccountRepository"):
                with patch("backend.app.services.aa_service.AAFetchedDataRepository"):
                    svc = AccountAggregatorService(mock_db)
                    with pytest.raises(ValueError, match="not ACTIVE"):
                        await svc.initiate_fetch(user_id, sample_consent.id)

    @pytest.mark.asyncio
    async def test_handle_consent_webhook_updates_status(
        self, user_id, mock_db, sample_consent
    ):
        """Webhook handler should update consent status."""
        from backend.app.services.aa_service import AccountAggregatorService

        sample_consent.status = ConsentStatus.PENDING

        with patch(
            "backend.app.services.aa_service.AAConsentRepository"
        ) as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_handle.return_value = sample_consent
            mock_repo.update_status = AsyncMock()
            MockRepo.return_value = mock_repo

            with patch("backend.app.services.aa_service.AALinkedAccountRepository"):
                with patch("backend.app.services.aa_service.AAFetchedDataRepository"):
                    svc = AccountAggregatorService(mock_db)
                    result = await svc.handle_consent_webhook(
                        consent_handle="HDL-TEST123",
                        new_status=ConsentStatus.ACTIVE,
                        consent_id_str="CNS-NEW",
                        reason=None,
                        raw={"status": "ACTIVE"},
                    )

        mock_repo.update_status.assert_called_once()
        call_kwargs = mock_repo.update_status.call_args
        assert call_kwargs.kwargs["status"] == ConsentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_webhook_unknown_handle_returns_none(self, mock_db):
        """Unknown consent handle should return None gracefully."""
        from backend.app.services.aa_service import AccountAggregatorService

        with patch(
            "backend.app.services.aa_service.AAConsentRepository"
        ) as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_handle.return_value = None
            MockRepo.return_value = mock_repo

            with patch("backend.app.services.aa_service.AALinkedAccountRepository"):
                with patch("backend.app.services.aa_service.AAFetchedDataRepository"):
                    svc = AccountAggregatorService(mock_db)
                    result = await svc.handle_consent_webhook(
                        consent_handle="INVALID",
                        new_status=ConsentStatus.ACTIVE,
                        consent_id_str=None,
                        reason=None,
                        raw=None,
                    )

        assert result is None


# ── PhysicalAssetService tests ────────────────────────────────────────────────

class TestPhysicalAssetService:

    @pytest.mark.asyncio
    async def test_add_asset(self, user_id, mock_db, sample_physical_asset):
        from backend.app.services.asset_service import PhysicalAssetService

        req = PhysicalAssetCreateRequest(
            category=AssetCategory.REAL_ESTATE,
            name="2BHK Apartment Bandra",
            current_value=Decimal("8500000"),
            valuation_date=date(2024, 11, 1),
            valuation_method=ValuationMethod.GOVT_CIRCLE_RATE,
            outstanding_loan=Decimal("2200000"),
        )

        with patch(
            "backend.app.services.asset_service.PhysicalAssetRepository"
        ) as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.create.return_value = sample_physical_asset
            MockRepo.return_value = mock_repo

            svc = PhysicalAssetService(mock_db)
            result = await svc.add_asset(user_id, req)

        assert result.category == AssetCategory.REAL_ESTATE
        assert result.effective_value == Decimal("6300000.00")
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_asset_retires_old_and_creates_new(
        self, user_id, mock_db, sample_physical_asset
    ):
        from backend.app.services.asset_service import PhysicalAssetService

        updated_asset = PhysicalAsset(
            id=uuid.uuid4(),
            user_id=user_id,
            category=AssetCategory.REAL_ESTATE,
            name="2BHK Apartment Bandra",
            current_value=Decimal("9200000.00"),  # updated value
            valuation_date=date(2024, 12, 1),
            valuation_method=ValuationMethod.PROFESSIONAL,
            outstanding_loan=Decimal("2100000.00"),
            ownership_percentage=Decimal("100"),
            is_current=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        with patch(
            "backend.app.services.asset_service.PhysicalAssetRepository"
        ) as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_user_asset.return_value = sample_physical_asset
            mock_repo.soft_retire = AsyncMock()
            mock_repo.create.return_value = updated_asset
            MockRepo.return_value = mock_repo

            svc = PhysicalAssetService(mock_db)
            req = PhysicalAssetUpdateRequest(
                current_value=Decimal("9200000"),
                valuation_date=date(2024, 12, 1),
                valuation_method=ValuationMethod.PROFESSIONAL,
            )
            result = await svc.update_asset(user_id, sample_physical_asset.id, req)

        # Old record should be retired
        mock_repo.soft_retire.assert_called_once_with(sample_physical_asset.id)
        # New record should be created
        mock_repo.create.assert_called_once()
        assert result.current_value == Decimal("9200000.00")

    @pytest.mark.asyncio
    async def test_update_asset_not_found_raises(self, user_id, mock_db):
        from backend.app.services.asset_service import PhysicalAssetService

        with patch(
            "backend.app.services.asset_service.PhysicalAssetRepository"
        ) as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_user_asset.return_value = None
            MockRepo.return_value = mock_repo

            svc = PhysicalAssetService(mock_db)
            with pytest.raises(ValueError, match="not found"):
                await svc.update_asset(
                    user_id,
                    uuid.uuid4(),
                    PhysicalAssetUpdateRequest(current_value=Decimal("1000000")),
                )


# ── NetWorthService tests ─────────────────────────────────────────────────────

class TestNetWorthService:

    @pytest.mark.asyncio
    async def test_recompute_aggregates_all_sources(
        self, user_id, mock_db
    ):
        """Net worth = financial + AA + physical - liabilities."""
        from backend.app.services.asset_service import NetWorthService

        snapshot = NetWorthSnapshot(
            id=uuid.uuid4(),
            user_id=user_id,
            financial_assets=Decimal("430000"),
            aa_assets=Decimal("423500"),
            physical_assets=Decimal("8500000"),
            total_liabilities=Decimal("2200000"),
            gross_assets=Decimal("9353500"),
            net_worth=Decimal("7153500"),
            computed_at=datetime.now(timezone.utc),
        )

        with patch(
            "backend.app.services.asset_service.NetWorthSnapshotRepository"
        ) as MockSnapRepo, patch(
            "backend.app.services.asset_service.PhysicalAssetRepository"
        ) as MockAssetRepo, patch(
            "backend.app.services.asset_service.AALinkedAccountRepository"
        ) as MockAARepo:

            mock_snap_repo = AsyncMock()
            mock_snap_repo.create.return_value = snapshot
            MockSnapRepo.return_value = mock_snap_repo

            mock_asset_repo = AsyncMock()
            mock_asset_repo.total_effective_value_for_user.return_value = Decimal("6300000")
            mock_asset_repo.total_liabilities_for_user.return_value = Decimal("2200000")
            mock_asset_repo.summary_by_category.return_value = {}
            MockAssetRepo.return_value = mock_asset_repo

            mock_aa_repo = AsyncMock()
            mock_aa_repo.total_balance_for_user.return_value = 423500.0
            MockAARepo.return_value = mock_aa_repo

            # Mock DB execute for WealthProfile query
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = MagicMock(
                total_savings=Decimal("250000"),
                total_investments=Decimal("180000"),
            )
            mock_db.execute.return_value = mock_result

            svc = NetWorthService(mock_db)
            result = await svc.recompute(user_id)

        mock_snap_repo.create.assert_called_once()
        assert result.snapshot_id == snapshot.id

    @pytest.mark.asyncio
    async def test_get_latest_returns_none_when_no_snapshot(self, user_id, mock_db):
        from backend.app.services.asset_service import NetWorthService

        with patch(
            "backend.app.services.asset_service.NetWorthSnapshotRepository"
        ) as MockRepo, patch(
            "backend.app.services.asset_service.PhysicalAssetRepository"
        ), patch(
            "backend.app.services.asset_service.AALinkedAccountRepository"
        ):
            mock_repo = AsyncMock()
            mock_repo.latest_for_user.return_value = None
            MockRepo.return_value = mock_repo

            svc = NetWorthService(mock_db)
            result = await svc.get_latest(user_id)

        assert result is None


# ── AAGatewayClient sandbox tests ─────────────────────────────────────────────

class TestAAGatewayClientSandbox:

    @pytest.mark.asyncio
    async def test_sandbox_consent_returns_handle(self):
        from backend.app.services.aa_service import AAGatewayClient

        client = AAGatewayClient("finvu")
        assert client.is_sandbox is True  # dev environment

        result = await client.raise_consent({"test": True})
        assert "ConsentHandle" in result
        assert result["ConsentHandle"].startswith("HDL-")

    @pytest.mark.asyncio
    async def test_sandbox_fi_request_returns_session_id(self):
        from backend.app.services.aa_service import AAGatewayClient

        client = AAGatewayClient("finvu")
        result = await client.initiate_fi_request({"test": True})
        assert "sessionId" in result
        assert result["sessionId"].startswith("SES-")

    @pytest.mark.asyncio
    async def test_sandbox_fi_data_returns_two_fips(self):
        from backend.app.services.aa_service import AAGatewayClient

        client = AAGatewayClient("finvu")
        result = await client.fetch_fi_data("SES-TEST")
        assert result["status"] == "READY"
        fips = [fi["fipID"] for fi in result["FI"]]
        assert "HDFC-FIP" in fips
        assert "SBI-FIP" in fips


# ── Encryption round-trip test ────────────────────────────────────────────────

class TestEncryption:

    def test_fernet_round_trip(self):
        """Ensure encrypt → decrypt round-trip works for AA payloads."""
        from cryptography.fernet import Fernet
        from backend.app.services.aa_service import _encrypt, _decrypt
        from unittest.mock import patch

        test_key = Fernet.generate_key().decode()
        payload = '{"balance": 325000, "account": "XXXX4521"}'

        with patch("backend.app.services.aa_service.settings") as mock_settings:
            mock_settings.FERNET_KEY = test_key
            encrypted = _encrypt(payload)
            decrypted = _decrypt(encrypted)

        assert decrypted == payload
        assert encrypted != payload
