"""
SecureWealth Twin — Account Aggregator Service.

Orchestrates the full AA consent + data-fetch lifecycle:
  1. Raise a consent request to the AA gateway
  2. Poll / receive webhook for consent approval
  3. Initiate a data-fetch session (FI Data Request)
  4. Decrypt, parse, and store FIP response
  5. Update linked-account balances in DB
  6. Emit audit events at every state change

AA gateway calls go through AAGatewayClient (httpx-based).
In sandbox mode the client returns realistic mock responses.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.models.aa_consent import (
    AAConsent,
    AAFetchedData,
    AALinkedAccount,
    AccountType,
    ConsentStatus,
    FetchStatus,
)
from backend.app.repositories.aa_repository import (
    AAConsentRepository,
    AAFetchedDataRepository,
    AALinkedAccountRepository,
)
from backend.app.schemas.aa_schemas import (
    ConsentCreateRequest,
    FinancialPictureResponse,
    LinkedAccountResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# ── AA Gateway Client (httpx wrapper) ─────────────────────────────────────────

class AAGatewayClient:
    """
    Thin async HTTP client for the AA Sahamati/Finvu API.

    In SANDBOX mode (ENVIRONMENT != production) returns deterministic
    mock payloads so development requires no live AA credentials.
    """

    SANDBOX_AA_URLS = {
        "finvu": "https://api.sandbox.finvu.in/v2",
        "onemoney": "https://api.sandbox.onemoney.in/v2",
        "anumati": "https://api.sandbox.anumati.in/v2",
    }

    PROD_AA_URLS = {
        "finvu": "https://api.finvu.in/v2",
        "onemoney": "https://api.onemoney.in/v2",
        "anumati": "https://api.anumati.in/v2",
    }

    def __init__(self, aa_id: str) -> None:
        self.aa_id = aa_id
        self.is_sandbox = settings.ENVIRONMENT != "production"
        base_urls = self.SANDBOX_AA_URLS if self.is_sandbox else self.PROD_AA_URLS
        self.base_url = base_urls.get(aa_id, f"https://api.{aa_id}.in/v2")

    async def raise_consent(self, payload: dict) -> dict:
        """POST /Consent — raises a consent request to the AA."""
        if self.is_sandbox:
            return self._mock_consent_response(payload)

        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/Consent",
                json=payload,
                headers=self._auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def fetch_consent_status(self, consent_handle: str) -> dict:
        """GET /Consent/handle/{handle} — poll consent status."""
        if self.is_sandbox:
            return {"status": "ACTIVE", "consentId": f"CNS-{consent_handle[:8]}"}

        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{self.base_url}/Consent/handle/{consent_handle}",
                headers=self._auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def initiate_fi_request(self, payload: dict) -> dict:
        """POST /FI/request — trigger financial information fetch from FIPs."""
        if self.is_sandbox:
            return self._mock_fi_request_response(payload)

        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/FI/request",
                json=payload,
                headers=self._auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def fetch_fi_data(self, session_id: str) -> dict:
        """GET /FI/fetch/{sessionId} — fetch decrypted FI data."""
        if self.is_sandbox:
            return self._mock_fi_data(session_id)

        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.base_url}/FI/fetch/{session_id}",
                headers=self._auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()

    # ── Auth helpers ──────────────────────────────────────────────

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {settings.SECRET_KEY}",
            "x-jws-signature": "placeholder",
            "Content-Type": "application/json",
        }

    # ── Sandbox mock responses ────────────────────────────────────

    def _mock_consent_response(self, payload: dict) -> dict:
        handle = f"HDL-{uuid.uuid4().hex[:12].upper()}"
        return {
            "ver": "2.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ConsentHandle": handle,
        }

    def _mock_fi_request_response(self, payload: dict) -> dict:
        session_id = f"SES-{uuid.uuid4().hex[:16].upper()}"
        return {
            "ver": "2.0.0",
            "sessionId": session_id,
            "status": "PENDING",
        }

    def _mock_fi_data(self, session_id: str) -> dict:
        """Return realistic mock FI data for sandbox testing."""
        return {
            "ver": "2.0.0",
            "status": "READY",
            "FI": [
                {
                    "fipID": "HDFC-FIP",
                    "data": [
                        {
                            "linkRefNumber": "REF001",
                            "maskedAccNumber": "XXXX4521",
                            "decryptedFI": json.dumps({
                                "account": {
                                    "type": "savings",
                                    "maskedAccNumber": "XXXX4521",
                                    "ifscCode": "HDFC0001234",
                                    "balance": 325000.00,
                                    "currency": "INR",
                                },
                                "transactions": [
                                    {"amount": 50000, "type": "credit", "date": "2024-11-01"},
                                    {"amount": 12000, "type": "debit",  "date": "2024-11-05"},
                                ],
                            }),
                        }
                    ],
                },
                {
                    "fipID": "SBI-FIP",
                    "data": [
                        {
                            "linkRefNumber": "REF002",
                            "maskedAccNumber": "XXXX7890",
                            "decryptedFI": json.dumps({
                                "account": {
                                    "type": "savings",
                                    "maskedAccNumber": "XXXX7890",
                                    "ifscCode": "SBIN0001234",
                                    "balance": 98500.00,
                                    "currency": "INR",
                                },
                                "transactions": [],
                            }),
                        }
                    ],
                },
            ],
        }


# ── Encryption helpers ────────────────────────────────────────────────────────

def _encrypt(data: str) -> str:
    f = Fernet(settings.FERNET_KEY.encode())
    return f.encrypt(data.encode()).decode()


def _decrypt(token: str) -> str:
    f = Fernet(settings.FERNET_KEY.encode())
    return f.decrypt(token.encode()).decode()


# ── Service ───────────────────────────────────────────────────────────────────

class AccountAggregatorService:
    """
    Business logic layer for the Account Aggregator integration.

    Injected with an AsyncSession; repositories are instantiated internally.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.consent_repo  = AAConsentRepository(db)
        self.account_repo  = AALinkedAccountRepository(db)
        self.fetch_repo    = AAFetchedDataRepository(db)

    # ── Consent management ─────────────────────────────────────────

    async def create_consent(
        self, user_id: uuid.UUID, req: ConsentCreateRequest
    ) -> AAConsent:
        """
        Raise a consent request to the AA and persist the consent artefact.
        Returns the AAConsent with PENDING status; approval happens out-of-band
        (user completes flow on AA app, then webhook arrives).
        """
        client = AAGatewayClient(req.aa_id)

        now = datetime.now(timezone.utc)
        expiry = now + timedelta(days=req.consent_duration_days)
        date_from = now - timedelta(days=req.date_range_months * 30)

        aa_payload = {
            "ver": "2.0.0",
            "timestamp": now.isoformat(),
            "txnid": str(uuid.uuid4()),
            "ConsentDetail": {
                "consentStart": now.isoformat(),
                "consentExpiry": expiry.isoformat(),
                "consentMode": "VIEW",
                "fetchType": "PERIODIC",
                "consentTypes": ["TRANSACTIONS", "SUMMARY", "PROFILE"],
                "fiTypes": req.fi_types,
                "DataConsumer": {"id": "SECUREWEALTH-FIU"},
                "Customer": {"id": str(user_id)},
                "Purpose": {"code": req.purpose_code},
                "FIDataRange": {
                    "from": date_from.isoformat(),
                    "to": now.isoformat(),
                },
                "DataLife": {"unit": "MONTH", "value": req.consent_duration_days // 30},
                "Frequency": {"unit": req.fetch_frequency, "value": 1},
            },
        }

        try:
            aa_response = await client.raise_consent(aa_payload)
        except Exception as exc:
            logger.error("AA consent raise failed: %s", exc)
            aa_response = {}

        consent = AAConsent(
            user_id=user_id,
            aa_id=req.aa_id,
            consent_handle=aa_response.get("ConsentHandle"),
            status=ConsentStatus.PENDING,
            purpose_code=req.purpose_code,
            fi_types=req.fi_types,
            date_range_from=date_from,
            date_range_to=now,
            consent_expiry=expiry,
            fetch_frequency=req.fetch_frequency,
            raw_response=aa_response,
        )
        return await self.consent_repo.create(consent)

    async def handle_consent_webhook(
        self,
        consent_handle: str,
        new_status: ConsentStatus,
        consent_id_str: str | None,
        reason: str | None,
        raw: dict | None,
    ) -> AAConsent | None:
        """
        Process an inbound webhook from the AA notifying consent status change.
        Called by the /webhook/aa-consent route (unauthenticated, HMAC-verified).
        """
        consent = await self.consent_repo.get_by_handle(consent_handle)
        if not consent:
            logger.warning("Webhook for unknown consent handle: %s", consent_handle)
            return None

        await self.consent_repo.update_status(
            consent_id_pk=consent.id,
            status=new_status,
            consent_id_str=consent_id_str,
            reason=reason,
            raw_response=raw,
        )
        logger.info("Consent %s → %s", consent_handle, new_status)
        return consent

    async def list_consents(
        self, user_id: uuid.UUID, status: ConsentStatus | None = None
    ) -> list[AAConsent]:
        return await self.consent_repo.list_for_user(user_id, status=status)

    async def revoke_consent(self, user_id: uuid.UUID, consent_pk: uuid.UUID) -> AAConsent:
        consent = await self.consent_repo.get_by_id(consent_pk)
        if not consent or consent.user_id != user_id:
            raise ValueError("Consent not found or access denied")

        # Optionally call AA revocation API in production
        await self.consent_repo.update_status(consent_pk, ConsentStatus.REVOKED)
        await self.session.refresh(consent)
        return consent

    # ── Data fetch ─────────────────────────────────────────────────

    async def initiate_fetch(
        self,
        user_id: uuid.UUID,
        consent_pk: uuid.UUID,
        fi_types: list[str] | None = None,
    ) -> list[AAFetchedData]:
        """
        Trigger an FI Data Request for an active consent.
        Persists one AAFetchedData row per fi_type per FIP and returns them.
        """
        consent = await self.consent_repo.get_by_id(consent_pk)
        if not consent or consent.user_id != user_id:
            raise ValueError("Consent not found or access denied")
        if consent.status != ConsentStatus.ACTIVE:
            raise ValueError(f"Consent is not ACTIVE (status={consent.status})")

        client = AAGatewayClient(consent.aa_id)
        types_to_fetch = fi_types or consent.fi_types or ["DEPOSIT"]

        now = datetime.now(timezone.utc)
        fi_payload = {
            "ver": "2.0.0",
            "timestamp": now.isoformat(),
            "txnid": str(uuid.uuid4()),
            "FIDataRange": {
                "from": (consent.date_range_from or now - timedelta(days=365)).isoformat(),
                "to": now.isoformat(),
            },
            "Consent": {
                "id": consent.consent_id,
                "digitalSignature": "placeholder",
            },
        }

        try:
            fi_response = await client.initiate_fi_request(fi_payload)
            session_id = fi_response.get("sessionId", str(uuid.uuid4()))
        except Exception as exc:
            logger.error("FI request failed: %s", exc)
            session_id = f"ERR-{uuid.uuid4().hex[:8]}"

        records = []
        for fi_type in types_to_fetch:
            record = AAFetchedData(
                user_id=user_id,
                consent_id=consent.id,
                session_id=session_id,
                fi_type=fi_type,
                status=FetchStatus.INITIATED,
            )
            records.append(await self.fetch_repo.create(record))

        # Immediately try to retrieve data (sandbox resolves instantly)
        await self._process_fi_data(session_id, user_id, consent, records)

        return records

    async def _process_fi_data(
        self,
        session_id: str,
        user_id: uuid.UUID,
        consent: AAConsent,
        fetch_records: list[AAFetchedData],
    ) -> None:
        """
        Pull FI data from AA, decrypt, parse, and persist.
        Updates AALinkedAccount balances and fetch record summaries.
        """
        client = AAGatewayClient(consent.aa_id)
        try:
            fi_data = await client.fetch_fi_data(session_id)
        except Exception as exc:
            logger.error("FI fetch failed: %s", exc)
            for rec in fetch_records:
                rec.status = FetchStatus.FAILED
                rec.fetch_error = str(exc)
            return

        fip_data_list = fi_data.get("FI", [])

        for fip_block in fip_data_list:
            fip_id = fip_block.get("fipID", "UNKNOWN")
            for acct_data in fip_block.get("data", []):
                raw_fi_str = acct_data.get("decryptedFI", "{}")
                try:
                    fi_json = json.loads(raw_fi_str)
                except json.JSONDecodeError:
                    continue

                account_info = fi_json.get("account", {})
                balance = float(account_info.get("balance", 0))
                acct_type_str = account_info.get("type", "savings").upper()
                acct_type = AccountType.SAVINGS
                for at in AccountType:
                    if at.value.upper() == acct_type_str:
                        acct_type = at
                        break

                # Upsert linked account
                linked = await self.account_repo.upsert_account(
                    user_id=user_id,
                    consent_id=consent.id,
                    fip_id=fip_id,
                    account_ref=acct_data.get("linkRefNumber", str(uuid.uuid4())),
                    defaults={
                        "fip_name": fip_id.replace("-FIP", ""),
                        "account_type": acct_type,
                        "masked_account_number": account_info.get("maskedAccNumber"),
                        "ifsc": account_info.get("ifscCode"),
                        "current_balance": Decimal(str(balance)),
                        "currency": account_info.get("currency", "INR"),
                        "last_fetched_at": datetime.now(timezone.utc),
                    },
                )

                # Encrypt and store raw payload
                encrypted = _encrypt(raw_fi_str)
                summary = {
                    "balance": balance,
                    "transactions_count": len(fi_json.get("transactions", [])),
                    "fip_id": fip_id,
                    "masked_account": account_info.get("maskedAccNumber"),
                }

                # Update fetch record for matching fi_type
                for rec in fetch_records:
                    if rec.status == FetchStatus.INITIATED:
                        rec.status = FetchStatus.SUCCESS
                        rec.encrypted_payload = encrypted
                        rec.summary = summary
                        rec.fetched_at = datetime.now(timezone.utc)
                        rec.linked_account_id = linked.id
                        break

        # Mark any still-INITIATED as partial
        for rec in fetch_records:
            if rec.status == FetchStatus.INITIATED:
                rec.status = FetchStatus.PARTIAL

    # ── Financial picture ──────────────────────────────────────────

    async def get_financial_picture(
        self, user_id: uuid.UUID
    ) -> FinancialPictureResponse:
        """
        Returns a consolidated view of all AA-linked accounts and their balances.
        """
        consents = await self.consent_repo.list_for_user(user_id)
        active_consents = [c for c in consents if c.status == ConsentStatus.ACTIVE]
        accounts = await self.account_repo.list_for_user(user_id, active_only=True)

        total_balance = sum(Decimal(str(a.current_balance)) for a in accounts)
        last_updated = max(
            (a.last_fetched_at for a in accounts if a.last_fetched_at),
            default=None,
        )

        return FinancialPictureResponse(
            user_id=user_id,
            total_aa_balance=total_balance,
            accounts=[LinkedAccountResponse.model_validate(a) for a in accounts],
            last_updated=last_updated,
            consent_count=len(consents),
            active_consent_count=len(active_consents),
        )
