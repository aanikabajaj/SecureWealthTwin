"""
SecureWealth Twin — API Integration Tests: Aggregator, Assets, NetWorth endpoints.

Uses FastAPI TestClient with a mocked DB session and auth dependency override.

Run with:
    pytest backend/app/tests/test_api_endpoints.py -v --asyncio-mode=auto
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.models.aa_consent import AAConsent, ConsentStatus, AALinkedAccount, AccountType
from backend.app.models.physical_asset import (
    AssetCategory, PhysicalAsset, ValuationMethod, OwnershipType
)
from backend.app.models.networth_snapshot import NetWorthSnapshot
from backend.app.models.user import User, UserRole


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def test_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="test@securewealth.in",
        hashed_password="hashed",
        full_name="Test User",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_mfa_enabled=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def app_client(test_user):
    """FastAPI test client with auth and DB overrides."""
    from backend.app.main import app
    from backend.app.db.database import get_db
    from backend.app.middleware.auth_middleware import get_current_user

    async def override_get_db():
        db = AsyncMock()
        db.commit = AsyncMock()
        db.flush = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        yield db

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_consent_response(test_user) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "aa_id": "finvu",
        "consent_handle": "HDL-TESTHANDLE",
        "consent_id": None,
        "status": "pending",
        "fi_types": ["DEPOSIT", "MUTUAL_FUNDS"],
        "fetch_frequency": "MONTHLY",
        "consent_expiry": "2025-06-01T00:00:00+00:00",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_asset_response(test_user) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "user_id": str(test_user.id),
        "category": "real_estate",
        "name": "2BHK Apartment Bandra",
        "description": None,
        "current_value": "8500000.00",
        "purchase_value": "5000000.00",
        "purchase_date": "2018-03-15",
        "valuation_date": "2024-11-01",
        "valuation_method": "govt_circle_rate",
        "outstanding_loan": "2200000.00",
        "ownership_type": "sole",
        "ownership_percentage": "100.00",
        "effective_value": "6300000.00",
        "unrealised_gain": "3500000.00",
        "metadata_json": None,
        "document_urls": None,
        "include_in_networth": True,
        "is_current": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Aggregator endpoint tests ─────────────────────────────────────────────────

class TestAggregatorEndpoints:

    def test_create_consent_returns_201(self, app_client, sample_consent_response):
        with patch(
            "backend.app.api.v1.routers.aggregator.AccountAggregatorService"
        ) as MockSvc:
            mock_svc = AsyncMock()
            consent_obj = MagicMock()
            consent_obj.model_validate = MagicMock(return_value=sample_consent_response)

            # Patch ConsentResponse.model_validate to return our dict
            with patch(
                "backend.app.api.v1.routers.aggregator.ConsentResponse"
            ) as MockResponse:
                MockResponse.model_validate.return_value = sample_consent_response
                mock_svc.create_consent.return_value = MagicMock()
                MockSvc.return_value = mock_svc

                response = app_client.post(
                    "/api/v1/aggregator/consents",
                    json={
                        "aa_id": "finvu",
                        "fi_types": ["DEPOSIT"],
                        "consent_duration_days": 180,
                        "date_range_months": 12,
                    },
                )

        assert response.status_code == 201

    def test_create_consent_invalid_aa_id_returns_422(self, app_client):
        response = app_client.post(
            "/api/v1/aggregator/consents",
            json={"aa_id": "totally_fake_bank"},
        )
        assert response.status_code == 422

    def test_list_consents_returns_200(self, app_client):
        with patch(
            "backend.app.api.v1.routers.aggregator.AccountAggregatorService"
        ) as MockSvc, patch(
            "backend.app.api.v1.routers.aggregator.ConsentResponse"
        ) as MockResponse:
            mock_svc = AsyncMock()
            mock_svc.list_consents.return_value = []
            MockSvc.return_value = mock_svc
            MockResponse.model_validate.return_value = {}

            response = app_client.get("/api/v1/aggregator/consents")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_financial_picture_returns_200(self, app_client, test_user):
        with patch(
            "backend.app.api.v1.routers.aggregator.AccountAggregatorService"
        ) as MockSvc:
            mock_svc = AsyncMock()
            mock_svc.get_financial_picture.return_value = MagicMock(
                user_id=test_user.id,
                total_aa_balance=Decimal("423500"),
                accounts=[],
                last_updated=None,
                consent_count=1,
                active_consent_count=1,
                model_dump=lambda: {
                    "user_id": str(test_user.id),
                    "total_aa_balance": "423500",
                    "accounts": [],
                    "last_updated": None,
                    "consent_count": 1,
                    "active_consent_count": 1,
                },
            )
            MockSvc.return_value = mock_svc

            response = app_client.get("/api/v1/aggregator/financial-picture")

        assert response.status_code == 200

    def test_webhook_invalid_signature_returns_401(self, app_client):
        response = app_client.post(
            "/api/v1/aggregator/webhook/consent-status",
            json={"ConsentHandle": "HDL-TEST", "status": "ACTIVE"},
            headers={"X-AA-Signature": "invalidsignature"},
        )
        assert response.status_code == 401

    def test_revoke_consent_not_found_returns_404(self, app_client):
        with patch(
            "backend.app.api.v1.routers.aggregator.AccountAggregatorService"
        ) as MockSvc:
            mock_svc = AsyncMock()
            mock_svc.revoke_consent.side_effect = ValueError("not found")
            MockSvc.return_value = mock_svc

            response = app_client.delete(
                f"/api/v1/aggregator/consents/{uuid.uuid4()}"
            )

        assert response.status_code == 404


# ── Physical Assets endpoint tests ────────────────────────────────────────────

class TestAssetsEndpoints:

    def test_add_asset_returns_201(self, app_client, sample_asset_response):
        with patch(
            "backend.app.api.v1.routers.assets.PhysicalAssetService"
        ) as MockSvc:
            mock_svc = AsyncMock()
            mock_svc.add_asset.return_value = MagicMock(**sample_asset_response)
            MockSvc.return_value = mock_svc

            response = app_client.post(
                "/api/v1/assets",
                json={
                    "category": "real_estate",
                    "name": "2BHK Apartment Bandra",
                    "current_value": 8500000,
                    "valuation_date": "2024-11-01",
                    "outstanding_loan": 2200000,
                },
            )

        assert response.status_code == 201

    def test_add_asset_missing_required_field_returns_422(self, app_client):
        response = app_client.post(
            "/api/v1/assets",
            json={
                "category": "real_estate",
                # missing name, current_value, valuation_date
            },
        )
        assert response.status_code == 422

    def test_list_assets_returns_200(self, app_client):
        with patch(
            "backend.app.api.v1.routers.assets.PhysicalAssetService"
        ) as MockSvc:
            mock_svc = AsyncMock()
            mock_svc.list_assets.return_value = []
            MockSvc.return_value = mock_svc

            response = app_client.get("/api/v1/assets")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_assets_with_category_filter(self, app_client):
        with patch(
            "backend.app.api.v1.routers.assets.PhysicalAssetService"
        ) as MockSvc:
            mock_svc = AsyncMock()
            mock_svc.list_assets.return_value = []
            MockSvc.return_value = mock_svc

            response = app_client.get("/api/v1/assets?category=gold")

        assert response.status_code == 200
        mock_svc.list_assets.assert_called_once()

    def test_get_asset_not_found_returns_404(self, app_client):
        with patch(
            "backend.app.api.v1.routers.assets.PhysicalAssetService"
        ) as MockSvc:
            mock_svc = AsyncMock()
            mock_svc.get_asset.side_effect = ValueError("Asset not found")
            MockSvc.return_value = mock_svc

            response = app_client.get(f"/api/v1/assets/{uuid.uuid4()}")

        assert response.status_code == 404

    def test_delete_asset_returns_204(self, app_client):
        with patch(
            "backend.app.api.v1.routers.assets.PhysicalAssetService"
        ) as MockSvc:
            mock_svc = AsyncMock()
            mock_svc.delete_asset.return_value = None
            MockSvc.return_value = mock_svc

            response = app_client.delete(f"/api/v1/assets/{uuid.uuid4()}")

        assert response.status_code == 204

    def test_asset_summary_returns_200(self, app_client):
        with patch(
            "backend.app.api.v1.routers.assets.PhysicalAssetService"
        ) as MockSvc:
            mock_svc = AsyncMock()
            mock_svc.category_summary.return_value = []
            MockSvc.return_value = mock_svc

            response = app_client.get("/api/v1/assets/summary")

        assert response.status_code == 200


# ── Net Worth endpoint tests ──────────────────────────────────────────────────

class TestNetWorthEndpoints:

    def test_get_networth_no_snapshot_returns_404(self, app_client):
        with patch(
            "backend.app.api.v1.routers.networth.NetWorthService"
        ) as MockSvc:
            mock_svc = AsyncMock()
            mock_svc.get_latest.return_value = None
            MockSvc.return_value = mock_svc

            response = app_client.get("/api/v1/networth")

        assert response.status_code == 404

    def test_recompute_returns_200(self, app_client, test_user):
        with patch(
            "backend.app.api.v1.routers.networth.NetWorthService"
        ) as MockSvc:
            mock_svc = AsyncMock()
            mock_svc.recompute.return_value = MagicMock(
                message="Net worth recomputed successfully",
                snapshot_id=uuid.uuid4(),
                net_worth=Decimal("7153500"),
                computed_at=datetime.now(timezone.utc),
            )
            MockSvc.return_value = mock_svc

            response = app_client.post("/api/v1/networth/recompute")

        assert response.status_code == 200

    def test_networth_history_returns_list(self, app_client):
        with patch(
            "backend.app.api.v1.routers.networth.NetWorthService"
        ) as MockSvc:
            mock_svc = AsyncMock()
            mock_svc.get_history.return_value = []
            MockSvc.return_value = mock_svc

            response = app_client.get("/api/v1/networth/history?limit=6")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_networth_history_limit_validation(self, app_client):
        """limit > 60 should return 422."""
        response = app_client.get("/api/v1/networth/history?limit=100")
        assert response.status_code == 422
