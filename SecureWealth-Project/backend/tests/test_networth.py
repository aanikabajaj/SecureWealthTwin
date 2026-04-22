"""
SecureWealth Twin — Net Worth endpoint tests.
"""

import pytest
from httpx import AsyncClient
from decimal import Decimal

pytestmark = pytest.mark.asyncio

GOLD_PAYLOAD = {
    "category": "gold", "name": "Gold Bars",
    "current_value": 250000, "valuation_date": "2024-11-01",
    "valuation_method": "market_price", "outstanding_loan": 0,
    "include_in_networth": True,
}

PROPERTY_PAYLOAD = {
    "category": "real_estate", "name": "Mumbai Flat",
    "current_value": 9500000, "valuation_date": "2024-11-01",
    "valuation_method": "govt_circle_rate",
    "outstanding_loan": 3000000, "include_in_networth": True,
}


class TestNetWorth:

    async def test_get_networth_404_before_recompute(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/networth", headers=auth_headers)
        assert resp.status_code == 404
        assert "recompute" in resp.json()["detail"].lower()

    async def test_recompute_returns_snapshot(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/v1/networth/recompute", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "snapshot_id" in data
        assert "net_worth"   in data
        assert "computed_at" in data

    async def test_get_latest_after_recompute(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/v1/networth/recompute", headers=auth_headers)
        resp = await client.get("/api/v1/networth", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "snapshot_id"      in data
        assert "net_worth"        in data
        assert "gross_assets"     in data
        assert "financial_assets" in data
        assert "aa_assets"        in data
        assert "physical_assets"  in data

    async def test_physical_assets_included_in_networth(self, client: AsyncClient, auth_headers: dict):
        # Add gold asset
        await client.post("/api/v1/assets", headers=auth_headers, json=GOLD_PAYLOAD)
        resp = await client.post("/api/v1/networth/recompute", headers=auth_headers)
        data = resp.json()
        net_worth = float(data["net_worth"])
        # Gold has no loan so effective_value = 250000
        assert net_worth >= 250000

    async def test_liabilities_reduce_networth(self, client: AsyncClient, auth_headers: dict):
        # Add property with a large loan
        await client.post("/api/v1/assets", headers=auth_headers, json=PROPERTY_PAYLOAD)
        resp = await client.post("/api/v1/networth/recompute", headers=auth_headers)
        data = resp.json()
        # outstanding_loan (3000000) should appear in total_liabilities
        assert float(data["total_liabilities"]) >= 3000000

    async def test_recompute_twice_keeps_history(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/v1/networth/recompute", headers=auth_headers)
        await client.post("/api/v1/networth/recompute", headers=auth_headers)

        resp = await client.get("/api/v1/networth/history?limit=10", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    async def test_history_limit_param(self, client: AsyncClient, auth_headers: dict):
        for _ in range(3):
            await client.post("/api/v1/networth/recompute", headers=auth_headers)

        resp = await client.get("/api/v1/networth/history?limit=2", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) <= 2

    async def test_history_limit_too_large_rejected(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/networth/history?limit=999", headers=auth_headers)
        assert resp.status_code == 422

    async def test_breakdown_contains_all_buckets(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/v1/assets", headers=auth_headers, json=GOLD_PAYLOAD)
        await client.post("/api/v1/networth/recompute", headers=auth_headers)
        resp = await client.get("/api/v1/networth", headers=auth_headers)
        breakdown = resp.json().get("breakdown", {})
        assert "financial"  in breakdown
        assert "aa"         in breakdown
        assert "physical"   in breakdown
        assert "liabilities" in breakdown

    async def test_networth_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/networth")
        assert resp.status_code == 403

    async def test_recompute_requires_auth(self, client: AsyncClient):
        resp = await client.post("/api/v1/networth/recompute")
        assert resp.status_code == 403
