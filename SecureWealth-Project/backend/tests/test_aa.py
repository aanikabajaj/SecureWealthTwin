"""
SecureWealth Twin — Account Aggregator endpoint tests.
Sandbox mode (ENVIRONMENT=development) is always active in tests,
so no real AA credentials are needed.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

CONSENT_PAYLOAD = {
    "aa_id":                 "sandbox",
    "purpose_code":          "03",
    "fi_types":              ["DEPOSIT", "MUTUAL_FUNDS"],
    "fetch_frequency":       "MONTHLY",
    "consent_duration_days": 180,
    "date_range_months":     12,
}


# ── Consent tests ─────────────────────────────────────────────────────────────

class TestConsents:

    async def test_create_consent(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/v1/aggregator/consents",
                                 headers=auth_headers, json=CONSENT_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["aa_id"]           == "sandbox"
        assert data["status"]          == "pending"
        assert data["consent_handle"]  is not None
        assert data["fi_types"]        == ["DEPOSIT", "MUTUAL_FUNDS"]

    async def test_create_consent_unknown_aa(self, client: AsyncClient, auth_headers: dict):
        bad = {**CONSENT_PAYLOAD, "aa_id": "unknown_aa"}
        resp = await client.post("/api/v1/aggregator/consents",
                                 headers=auth_headers, json=bad)
        assert resp.status_code == 422

    async def test_list_consents(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/v1/aggregator/consents",
                          headers=auth_headers, json=CONSENT_PAYLOAD)
        resp = await client.get("/api/v1/aggregator/consents", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    async def test_list_consents_filter_by_status(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/v1/aggregator/consents",
                          headers=auth_headers, json=CONSENT_PAYLOAD)
        resp = await client.get("/api/v1/aggregator/consents?status_filter=pending",
                                headers=auth_headers)
        assert resp.status_code == 200
        for c in resp.json():
            assert c["status"] == "pending"

    async def test_get_consent_by_id(self, client: AsyncClient, auth_headers: dict):
        created = await client.post("/api/v1/aggregator/consents",
                                    headers=auth_headers, json=CONSENT_PAYLOAD)
        consent_id = created.json()["id"]
        resp = await client.get(f"/api/v1/aggregator/consents/{consent_id}",
                                headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == consent_id

    async def test_get_nonexistent_consent(self, client: AsyncClient, auth_headers: dict):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/api/v1/aggregator/consents/{fake_id}",
                                headers=auth_headers)
        assert resp.status_code == 404

    async def test_revoke_consent(self, client: AsyncClient, auth_headers: dict):
        created    = await client.post("/api/v1/aggregator/consents",
                                       headers=auth_headers, json=CONSENT_PAYLOAD)
        consent_id = created.json()["id"]
        resp = await client.delete(f"/api/v1/aggregator/consents/{consent_id}",
                                   headers=auth_headers)
        assert resp.status_code == 204

    async def test_consent_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/aggregator/consents")
        assert resp.status_code == 403


# ── Data Fetch tests ──────────────────────────────────────────────────────────

class TestFetch:

    async def _create_active_consent(self, client: AsyncClient, auth_headers: dict) -> str:
        """Create a consent and manually force it to ACTIVE status for fetch tests."""
        created = await client.post("/api/v1/aggregator/consents",
                                    headers=auth_headers, json=CONSENT_PAYLOAD)
        return created.json()["id"], created.json()["consent_handle"]

    async def test_fetch_rejected_for_pending_consent(self, client: AsyncClient, auth_headers: dict):
        consent_id, _ = await self._create_active_consent(client, auth_headers)
        resp = await client.post("/api/v1/aggregator/fetch", headers=auth_headers, json={
            "consent_id": consent_id,
        })
        # Pending consent → 400
        assert resp.status_code == 400
        assert "not ACTIVE" in resp.json()["detail"]

    async def test_list_fetch_sessions(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/aggregator/fetch", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_fetch_filter_by_fi_type(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/aggregator/fetch?fi_type=DEPOSIT",
                                headers=auth_headers)
        assert resp.status_code == 200


# ── Linked accounts & financial picture ───────────────────────────────────────

class TestLinkedAccounts:

    async def test_list_linked_accounts_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/aggregator/accounts", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_financial_picture_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/aggregator/financial-picture", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_aa_balance"      in data
        assert "accounts"              in data
        assert "consent_count"         in data
        assert "active_consent_count"  in data
        assert isinstance(data["accounts"], list)


# ── Webhook ───────────────────────────────────────────────────────────────────

class TestWebhook:

    async def test_webhook_invalid_hmac(self, client: AsyncClient):
        import json
        resp = await client.post(
            "/api/v1/aggregator/webhook/consent-status",
            content=json.dumps({"ConsentHandle": "HDL-ABC", "status": "ACTIVE"}),
            headers={
                "Content-Type":   "application/json",
                "X-AA-Signature": "badsignature",
            },
        )
        assert resp.status_code == 401

    async def test_webhook_valid_hmac(self, client: AsyncClient, auth_headers: dict):
        import hashlib
        import hmac as hmac_lib
        import json
        from backend.app.config import get_settings

        settings = get_settings()
        created  = await client.post("/api/v1/aggregator/consents",
                                     headers=auth_headers, json=CONSENT_PAYLOAD)
        handle   = created.json()["consent_handle"]

        body = json.dumps({"ConsentHandle": handle, "status": "ACTIVE"}).encode()
        sig  = hmac_lib.new(
            settings.AA_WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()

        resp = await client.post(
            "/api/v1/aggregator/webhook/consent-status",
            content=body,
            headers={"Content-Type": "application/json", "X-AA-Signature": sig},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Webhook processed"
