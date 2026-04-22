"""
SecureWealth Twin — Account Aggregator Service.
Fixed: revoke_consent bug (self.session → self.db), webhook HMAC uses AA_WEBHOOK_SECRET.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.aa_consent import (
    AAConsent, AAFetchedData, AALinkedAccount,
    AccountType, ConsentStatus, FetchStatus,
)
from app.repositories.aa_repository import (
    AAConsentRepository, AAFetchedDataRepository, AALinkedAccountRepository,
)
from app.schemas.aa_schemas import (
    ConsentCreateRequest, FinancialPictureResponse, LinkedAccountResponse,
)

logger   = logging.getLogger(__name__)
settings = get_settings()


# ── AA Gateway Client ─────────────────────────────────────────────────────────

class AAGatewayClient:
    """Thin async HTTP client. Sandbox mode returns deterministic mock data."""

    SANDBOX_URLS = {
        "finvu":     "https://api.sandbox.finvu.in/v2",
        "onemoney":  "https://api.sandbox.onemoney.in/v2",
        "anumati":   "https://api.sandbox.anumati.in/v2",
        "sandbox":   "https://api.sandbox.finvu.in/v2",
    }
    PROD_URLS = {
        "finvu":    "https://api.finvu.in/v2",
        "onemoney": "https://api.onemoney.in/v2",
        "anumati":  "https://api.anumati.in/v2",
    }

    def __init__(self, aa_id: str) -> None:
        self.aa_id      = aa_id
        self.is_sandbox = settings.ENVIRONMENT != "production"
        urls            = self.SANDBOX_URLS if self.is_sandbox else self.PROD_URLS
        self.base_url   = urls.get(aa_id, f"https://api.{aa_id}.in/v2")

    async def raise_consent(self, payload: dict) -> dict:
        if self.is_sandbox:
            return self._mock_consent_response(payload)
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{self.base_url}/Consent", json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def fetch_consent_status(self, handle: str) -> dict:
        if self.is_sandbox:
            return {"status": "ACTIVE", "consentId": f"CNS-{handle[:8]}"}
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{self.base_url}/Consent/handle/{handle}", headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def initiate_fi_request(self, payload: dict) -> dict:
        if self.is_sandbox:
            return self._mock_fi_request()
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{self.base_url}/FI/request", json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def fetch_fi_data(self, session_id: str) -> dict:
        if self.is_sandbox:
            return self._mock_fi_data(session_id)
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{self.base_url}/FI/fetch/{session_id}", headers=self._headers())
            r.raise_for_status()
            return r.json()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {settings.AA_FINVU_CLIENT_SECRET}",
            "x-jws-signature": "placeholder",
            "Content-Type": "application/json",
        }

    def _mock_consent_response(self, payload: dict) -> dict:
        import uuid as _uuid
        handle = f"HDL-{_uuid.uuid4().hex[:12].upper()}"
        return {"ver": "2.0.0", "timestamp": datetime.now(timezone.utc).isoformat(), "ConsentHandle": handle}

    def _mock_fi_request(self) -> dict:
        import uuid as _uuid
        session_id = f"SES-{_uuid.uuid4().hex[:16].upper()}"
        return {"ver": "2.0.0", "sessionId": session_id, "status": "PENDING"}

    def _mock_fi_data(self, session_id: str) -> dict:
        return {
            "ver": "2.0.0", "status": "READY",
            "FI": [
                {
                    "fipID": "HDFC-FIP",
                    "data": [{
                        "linkRefNumber": "REF001",
                        "maskedAccNumber": "XXXX4521",
                        "decryptedFI": json.dumps({
                            "account": {
                                "type": "savings", "maskedAccNumber": "XXXX4521",
                                "ifscCode": "HDFC0001234", "balance": 325000.00, "currency": "INR",
                            },
                            "transactions": [
                                {"amount": 50000, "type": "credit", "date": "2024-11-01"},
                                {"amount": 12000, "type": "debit",  "date": "2024-11-05"},
                            ],
                        }),
                    }],
                },
                {
                    "fipID": "SBI-FIP",
                    "data": [{
                        "linkRefNumber": "REF002",
                        "maskedAccNumber": "XXXX7890",
                        "decryptedFI": json.dumps({
                            "account": {
                                "type": "savings", "maskedAccNumber": "XXXX7890",
                                "ifscCode": "SBIN0001234", "balance": 98500.00, "currency": "INR",
                            },
                            "transactions": [],
                        }),
                    }],
                },
                {
                    "fipID": "ICICI-FIP",
                    "data": [{
                        "linkRefNumber": "REF003",
                        "maskedAccNumber": "XXXX2233",
                        "decryptedFI": json.dumps({
                            "account": {
                                "type": "mutual_fund", "maskedAccNumber": "XXXX2233",
                                "ifscCode": "", "balance": 452000.00, "currency": "INR",
                            },
                            "transactions": [],
                        }),
                    }],
                },
            ],
        }


# ── Encryption helpers ────────────────────────────────────────────────────────

def _encrypt(data: str) -> str:
    return Fernet(settings.FERNET_KEY.encode()).encrypt(data.encode()).decode()


def _decrypt(token: str) -> str:
    return Fernet(settings.FERNET_KEY.encode()).decrypt(token.encode()).decode()


# ── Service ───────────────────────────────────────────────────────────────────

class AccountAggregatorService:

    def __init__(self, db: AsyncSession) -> None:
        self.db           = db
        self.consent_repo = AAConsentRepository(db)
        self.account_repo = AALinkedAccountRepository(db)
        self.fetch_repo   = AAFetchedDataRepository(db)

    # ── Consent management ────────────────────────────────────────

    async def create_consent(self, user_id: uuid.UUID, req: ConsentCreateRequest) -> AAConsent:
        client = AAGatewayClient(req.aa_id)
        now    = datetime.now(timezone.utc)
        expiry = now + timedelta(days=req.consent_duration_days)
        d_from = now - timedelta(days=req.date_range_months * 30)

        payload = {
            "ver": "2.0.0",
            "timestamp": now.isoformat(),
            "txnid": str(uuid.uuid4()),
            "ConsentDetail": {
                "consentStart":  now.isoformat(),
                "consentExpiry": expiry.isoformat(),
                "consentMode":   "VIEW",
                "fetchType":     "PERIODIC",
                "consentTypes":  ["TRANSACTIONS", "SUMMARY", "PROFILE"],
                "fiTypes":       req.fi_types,
                "DataConsumer":  {"id": "SECUREWEALTH-FIU"},
                "Customer":      {"id": str(user_id)},
                "Purpose":       {"code": req.purpose_code},
                "FIDataRange":   {"from": d_from.isoformat(), "to": now.isoformat()},
                "DataLife":      {"unit": "MONTH", "value": req.consent_duration_days // 30},
                "Frequency":     {"unit": req.fetch_frequency, "value": 1},
            },
        }

        try:
            aa_resp = await client.raise_consent(payload)
        except Exception as exc:
            logger.error("AA consent raise failed: %s", exc)
            aa_resp = {}

        consent = AAConsent(
            user_id=user_id,
            aa_id=req.aa_id,
            consent_handle=aa_resp.get("ConsentHandle"),
            status=ConsentStatus.PENDING,
            purpose_code=req.purpose_code,
            fi_types=req.fi_types,
            date_range_from=d_from,
            date_range_to=now,
            consent_expiry=expiry,
            fetch_frequency=req.fetch_frequency,
            raw_response=aa_resp,
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
        consent = await self.consent_repo.get_by_handle(consent_handle)
        if not consent:
            logger.warning("Webhook for unknown handle: %s", consent_handle)
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
        await self.consent_repo.update_status(consent_pk, ConsentStatus.REVOKED)
        await self.db.refresh(consent)   # BUG FIX: was self.session.refresh
        return consent

    # ── Data fetch ────────────────────────────────────────────────

    async def initiate_fetch(
        self,
        user_id: uuid.UUID,
        consent_pk: uuid.UUID,
        fi_types: list[str] | None = None,
    ) -> list[AAFetchedData]:
        consent = await self.consent_repo.get_by_id(consent_pk)
        if not consent or consent.user_id != user_id:
            raise ValueError("Consent not found or access denied")
        if consent.status != ConsentStatus.ACTIVE:
            raise ValueError(f"Consent is not ACTIVE (status={consent.status})")

        client         = AAGatewayClient(consent.aa_id)
        types_to_fetch = fi_types or consent.fi_types or ["DEPOSIT"]
        now            = datetime.now(timezone.utc)

        fi_payload = {
            "ver": "2.0.0",
            "timestamp": now.isoformat(),
            "txnid": str(uuid.uuid4()),
            "FIDataRange": {
                "from": (consent.date_range_from or now - timedelta(days=365)).isoformat(),
                "to":   now.isoformat(),
            },
            "Consent": {"id": consent.consent_id, "digitalSignature": "placeholder"},
        }

        try:
            fi_resp    = await client.initiate_fi_request(fi_payload)
            session_id = fi_resp.get("sessionId", str(uuid.uuid4()))
        except Exception as exc:
            logger.error("FI request failed: %s", exc)
            session_id = f"ERR-{uuid.uuid4().hex[:8]}"

        records = []
        for fi_type in types_to_fetch:
            rec = AAFetchedData(
                user_id=user_id, consent_id=consent.id,
                session_id=session_id, fi_type=fi_type,
                status=FetchStatus.INITIATED,
            )
            records.append(await self.fetch_repo.create(rec))

        await self._process_fi_data(session_id, user_id, consent, records)
        return records

    async def _process_fi_data(
        self,
        session_id: str,
        user_id: uuid.UUID,
        consent: AAConsent,
        fetch_records: list[AAFetchedData],
    ) -> None:
        client = AAGatewayClient(consent.aa_id)
        try:
            fi_data = await client.fetch_fi_data(session_id)
        except Exception as exc:
            logger.error("FI fetch failed: %s", exc)
            for rec in fetch_records:
                rec.status      = FetchStatus.FAILED
                rec.fetch_error = str(exc)
            return

        for fip_block in fi_data.get("FI", []):
            fip_id = fip_block.get("fipID", "UNKNOWN")
            for acct_data in fip_block.get("data", []):
                raw_str = acct_data.get("decryptedFI", "{}")
                try:
                    fi_json = json.loads(raw_str)
                except json.JSONDecodeError:
                    continue

                account_info  = fi_json.get("account", {})
                balance       = float(account_info.get("balance", 0))
                acct_type_str = account_info.get("type", "savings").upper()
                acct_type     = AccountType.SAVINGS
                for at in AccountType:
                    if at.value.upper() == acct_type_str:
                        acct_type = at
                        break

                linked = await self.account_repo.upsert_account(
                    user_id=user_id, consent_id=consent.id,
                    fip_id=fip_id,
                    account_ref=acct_data.get("linkRefNumber", str(uuid.uuid4())),
                    defaults={
                        "fip_name":             fip_id.replace("-FIP", ""),
                        "account_type":         acct_type,
                        "masked_account_number": account_info.get("maskedAccNumber"),
                        "ifsc":                 account_info.get("ifscCode"),
                        "current_balance":      Decimal(str(balance)),
                        "currency":             account_info.get("currency", "INR"),
                        "last_fetched_at":      datetime.now(timezone.utc),
                    },
                )

                encrypted = _encrypt(raw_str)
                summary   = {
                    "balance":            balance,
                    "transactions_count": len(fi_json.get("transactions", [])),
                    "fip_id":             fip_id,
                    "masked_account":     account_info.get("maskedAccNumber"),
                }

                for rec in fetch_records:
                    if rec.status == FetchStatus.INITIATED:
                        rec.status            = FetchStatus.SUCCESS
                        rec.encrypted_payload = encrypted
                        rec.summary           = summary
                        rec.fetched_at        = datetime.now(timezone.utc)
                        rec.linked_account_id = linked.id
                        break

        for rec in fetch_records:
            if rec.status == FetchStatus.INITIATED:
                rec.status = FetchStatus.PARTIAL

    # ── Financial picture ─────────────────────────────────────────

    async def get_financial_picture(self, user_id: uuid.UUID) -> FinancialPictureResponse:
        consents        = await self.consent_repo.list_for_user(user_id)
        active_consents = [c for c in consents if c.status == ConsentStatus.ACTIVE]
        accounts        = await self.account_repo.list_for_user(user_id, active_only=True)
        total_balance   = sum(Decimal(str(a.current_balance)) for a in accounts)
        last_updated    = max(
            (a.last_fetched_at for a in accounts if a.last_fetched_at), default=None
        )
        return FinancialPictureResponse(
            user_id=user_id,
            total_aa_balance=total_balance,
            accounts=[LinkedAccountResponse.model_validate(a) for a in accounts],
            last_updated=last_updated,
            consent_count=len(consents),
            active_consent_count=len(active_consents),
        )
