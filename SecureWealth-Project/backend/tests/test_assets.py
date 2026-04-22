"""
SecureWealth Twin — Physical Assets endpoint tests.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

# ── Helpers ───────────────────────────────────────────────────────────────────

GOLD_PAYLOAD = {
    "category":        "gold",
    "name":            "Gold Coins",
    "current_value":   150000,
    "valuation_date":  "2024-11-01",
    "valuation_method":"self_declared",
    "outstanding_loan": 0,
    "metadata_json":   {"weight_grams": 50, "purity": "22K"},
    "include_in_networth": True,
}

PROPERTY_PAYLOAD = {
    "category":           "real_estate",
    "name":               "Flat in Andheri",
    "current_value":      8500000,
    "purchase_value":     6000000,
    "purchase_date":      "2019-04-15",
    "valuation_date":     "2024-11-01",
    "valuation_method":   "govt_circle_rate",
    "outstanding_loan":   2500000,
    "ownership_type":     "sole",
    "ownership_percentage": 100,
    "metadata_json":      {"location": "Mumbai", "area_sqft": 850},
    "include_in_networth": True,
}

VEHICLE_PAYLOAD = {
    "category":        "vehicle",
    "name":            "Honda City 2021",
    "current_value":   650000,
    "purchase_value":  1050000,
    "purchase_date":   "2021-06-01",
    "valuation_date":  "2024-11-01",
    "valuation_method":"market_price",
    "outstanding_loan": 120000,
    "metadata_json":   {"make": "Honda", "model": "City", "year": 2021},
    "include_in_networth": True,
}


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestAddAsset:

    async def test_add_gold(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/v1/assets", headers=auth_headers, json=GOLD_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["category"]      == "gold"
        assert data["name"]          == "Gold Coins"
        assert float(data["current_value"]) == 150000
        assert data["is_current"]    is True

    async def test_add_property_calculates_effective_value(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/v1/assets", headers=auth_headers, json=PROPERTY_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        # effective_value = current_value - outstanding_loan = 8500000 - 2500000 = 6000000
        assert float(data["effective_value"]) == 6000000.0
        # unrealised_gain = 8500000 - 6000000 = 2500000
        assert float(data["unrealised_gain"]) == 2500000.0

    async def test_add_vehicle(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/v1/assets", headers=auth_headers, json=VEHICLE_PAYLOAD)
        assert resp.status_code == 201

    async def test_add_requires_auth(self, client: AsyncClient):
        resp = await client.post("/api/v1/assets", json=GOLD_PAYLOAD)
        assert resp.status_code == 403

    async def test_add_invalid_category(self, client: AsyncClient, auth_headers: dict):
        bad = {**GOLD_PAYLOAD, "category": "crypto"}
        resp = await client.post("/api/v1/assets", headers=auth_headers, json=bad)
        assert resp.status_code == 422

    async def test_add_negative_value_rejected(self, client: AsyncClient, auth_headers: dict):
        bad = {**GOLD_PAYLOAD, "current_value": -1000}
        resp = await client.post("/api/v1/assets", headers=auth_headers, json=bad)
        assert resp.status_code == 422


class TestListAssets:

    async def test_list_all_assets(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/v1/assets", headers=auth_headers, json=GOLD_PAYLOAD)
        resp = await client.get("/api/v1/assets", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    async def test_filter_by_category(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/v1/assets", headers=auth_headers, json=GOLD_PAYLOAD)
        await client.post("/api/v1/assets", headers=auth_headers, json=VEHICLE_PAYLOAD)
        resp = await client.get("/api/v1/assets?category=gold", headers=auth_headers)
        assert resp.status_code == 200
        for item in resp.json():
            assert item["category"] == "gold"

    async def test_filter_invalid_category(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/assets?category=spaceship", headers=auth_headers)
        assert resp.status_code == 400


class TestGetAsset:

    async def test_get_by_id(self, client: AsyncClient, auth_headers: dict):
        created = await client.post("/api/v1/assets", headers=auth_headers, json=GOLD_PAYLOAD)
        asset_id = created.json()["id"]

        resp = await client.get(f"/api/v1/assets/{asset_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == asset_id

    async def test_get_nonexistent(self, client: AsyncClient, auth_headers: dict):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/api/v1/assets/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404


class TestUpdateAsset:

    async def test_update_value_creates_new_snapshot(self, client: AsyncClient, auth_headers: dict):
        created = await client.post("/api/v1/assets", headers=auth_headers, json=GOLD_PAYLOAD)
        old_id  = created.json()["id"]

        resp = await client.patch(f"/api/v1/assets/{old_id}", headers=auth_headers, json={
            "current_value":  175000,
            "valuation_date": "2025-01-01",
        })
        assert resp.status_code == 200
        new_data = resp.json()
        # New record has a different ID (old one is soft-retired)
        assert new_data["id"] != old_id
        assert float(new_data["current_value"]) == 175000
        assert new_data["is_current"] is True

    async def test_update_nonexistent(self, client: AsyncClient, auth_headers: dict):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.patch(f"/api/v1/assets/{fake_id}", headers=auth_headers, json={
            "current_value": 100000
        })
        assert resp.status_code == 404


class TestDeleteAsset:

    async def test_delete_soft_retires(self, client: AsyncClient, auth_headers: dict):
        created  = await client.post("/api/v1/assets", headers=auth_headers, json=GOLD_PAYLOAD)
        asset_id = created.json()["id"]

        resp = await client.delete(f"/api/v1/assets/{asset_id}", headers=auth_headers)
        assert resp.status_code == 204

        # After deletion it should no longer appear in the list
        list_resp = await client.get("/api/v1/assets", headers=auth_headers)
        ids = [a["id"] for a in list_resp.json()]
        assert asset_id not in ids

    async def test_delete_nonexistent(self, client: AsyncClient, auth_headers: dict):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.delete(f"/api/v1/assets/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404


class TestAssetSummary:

    async def test_summary_groups_by_category(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/v1/assets", headers=auth_headers, json=GOLD_PAYLOAD)
        await client.post("/api/v1/assets", headers=auth_headers, json=PROPERTY_PAYLOAD)

        resp = await client.get("/api/v1/assets/summary", headers=auth_headers)
        assert resp.status_code == 200
        summary = resp.json()
        categories = [s["category"] for s in summary]
        assert "gold"        in categories
        assert "real_estate" in categories

    async def test_summary_totals_are_correct(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/v1/assets", headers=auth_headers, json=GOLD_PAYLOAD)
        resp = await client.get("/api/v1/assets/summary", headers=auth_headers)
        gold_row = next(s for s in resp.json() if s["category"] == "gold")
        assert float(gold_row["total_value"])    >= 150000
        assert float(gold_row["total_effective_value"]) >= 150000
