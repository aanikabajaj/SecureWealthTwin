"""
SecureWealth Twin — Account Aggregator Router (FIXED).
Fixed: hmac.new → hmac.new() correct usage; webhook uses AA_WEBHOOK_SECRET not SECRET_KEY.
"""

import hashlib
import hmac
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.aa_consent import ConsentStatus
from app.models.user import User
from app.schemas.aa_schemas import (
    ConsentCreateRequest, ConsentResponse, ConsentStatusUpdateRequest,
    FetchInitiateRequest, FetchStatusResponse, FinancialPictureResponse,
    LinkedAccountResponse,
)
from app.services.aa_service import AccountAggregatorService

router   = APIRouter()
logger   = logging.getLogger(__name__)
settings = get_settings()


# ── Consent endpoints ─────────────────────────────────────────────────────────

@router.post(
    "/consents",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Raise a new AA consent request",
)
async def create_consent(
    req: ConsentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Raises a consent artefact with the specified Account Aggregator.
    Returns immediately with PENDING status. The user approves on the AA app
    (Finvu / OneMoney). Approval triggers the webhook below.
    In sandbox mode (ENVIRONMENT=development) the consent auto-resolves.
    """
    svc = AccountAggregatorService(db)
    try:
        consent = await svc.create_consent(current_user.id, req)
    except Exception as exc:
        logger.error("Consent creation failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"AA gateway error: {exc}")
    return ConsentResponse.model_validate(consent)


@router.get("/consents", response_model=list[ConsentResponse], summary="List all AA consents")
async def list_consents(
    status_filter: ConsentStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc      = AccountAggregatorService(db)
    consents = await svc.list_consents(current_user.id, status=status_filter)
    return [ConsentResponse.model_validate(c) for c in consents]


@router.get("/consents/{consent_id}", response_model=ConsentResponse, summary="Get a single consent")
async def get_consent(
    consent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.aa_repository import AAConsentRepository
    repo    = AAConsentRepository(db)
    consent = await repo.get_by_id(consent_id)
    if not consent or consent.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Consent not found")
    return ConsentResponse.model_validate(consent)


@router.delete("/consents/{consent_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke a consent")
async def revoke_consent(
    consent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AccountAggregatorService(db)
    try:
        await svc.revoke_consent(current_user.id, consent_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── Data fetch endpoints ───────────────────────────────────────────────────────

@router.post(
    "/fetch",
    response_model=list[FetchStatusResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate a financial data fetch from linked FIPs",
)
async def initiate_fetch(
    req: FetchInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers an FI Data Request against FIPs linked under the given consent.
    Returns one record per FI type. In sandbox mode resolves immediately with mock data.
    """
    svc = AccountAggregatorService(db)
    try:
        records = await svc.initiate_fetch(
            user_id=current_user.id, consent_pk=req.consent_id, fi_types=req.fi_types,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return [FetchStatusResponse.model_validate(r) for r in records]


@router.get("/fetch", response_model=list[FetchStatusResponse], summary="List all fetch sessions")
async def list_fetches(
    fi_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.aa_repository import AAFetchedDataRepository
    repo    = AAFetchedDataRepository(db)
    records = await repo.list_for_user(current_user.id, fi_type=fi_type)
    return [FetchStatusResponse.model_validate(r) for r in records]


# ── Financial picture ──────────────────────────────────────────────────────────

@router.get(
    "/financial-picture",
    response_model=FinancialPictureResponse,
    summary="Full cross-bank financial picture via Account Aggregator",
)
async def financial_picture(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns consolidated view of all bank accounts linked via AA,
    including total balance and per-account breakdown.
    """
    svc = AccountAggregatorService(db)
    return await svc.get_financial_picture(current_user.id)


# ── Linked accounts ────────────────────────────────────────────────────────────

@router.get("/accounts", response_model=list[LinkedAccountResponse], summary="List linked bank accounts")
async def list_linked_accounts(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.aa_repository import AALinkedAccountRepository
    repo     = AALinkedAccountRepository(db)
    accounts = await repo.list_for_user(current_user.id, active_only=active_only)
    return [LinkedAccountResponse.model_validate(a) for a in accounts]


# ── AA Webhook (unauthenticated, HMAC-verified) ────────────────────────────────

@router.post(
    "/webhook/consent-status",
    status_code=200,
    summary="Inbound webhook from AA for consent status changes",
    include_in_schema=False,
)
async def consent_status_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receives AA webhook events. Verifies X-AA-Signature HMAC-SHA256 before processing.
    Uses AA_WEBHOOK_SECRET (not SECRET_KEY) for proper secret separation.
    """
    body = await request.body()

    # HMAC verification — uses dedicated webhook secret
    signature = request.headers.get("X-AA-Signature", "")
    expected  = hmac.new(
        settings.AA_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        logger.warning("AA webhook: invalid HMAC signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    status_map = {
        "ACTIVE":  ConsentStatus.ACTIVE,
        "PAUSED":  ConsentStatus.PAUSED,
        "REVOKED": ConsentStatus.REVOKED,
        "EXPIRED": ConsentStatus.EXPIRED,
        "FAILED":  ConsentStatus.FAILED,
    }
    raw_status = payload.get("status", "").upper()
    new_status = status_map.get(raw_status, ConsentStatus.FAILED)

    svc = AccountAggregatorService(db)
    await svc.handle_consent_webhook(
        consent_handle=payload.get("ConsentHandle", ""),
        new_status=new_status,
        consent_id_str=payload.get("consentId"),
        reason=payload.get("reason"),
        raw=payload,
    )
    return {"message": "Webhook processed"}
