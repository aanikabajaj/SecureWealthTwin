"""
SecureWealth Twin — Background Workers.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from celery import Celery

from backend.app.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery(
    "securewealth_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "refresh-all-active-consents-daily": {
            "task": "backend.app.workers.aa_workers.refresh_all_active_consents",
            "schedule": 86400.0,
        },
        "expire-stale-consents-hourly": {
            "task": "backend.app.workers.aa_workers.expire_stale_consents",
            "schedule": 3600.0,
        },
    },
)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="backend.app.workers.aa_workers.refresh_aa_data_for_user",
    bind=True, max_retries=3, default_retry_delay=300,
)
def refresh_aa_data_for_user(self, user_id: str) -> dict:
    """Fetch fresh FI data from all FIPs for every ACTIVE consent of a user."""
    async def _run():
        from backend.app.db.database import AsyncSessionLocal
        from backend.app.models.aa_consent import ConsentStatus
        from backend.app.repositories.aa_repository import AAConsentRepository
        from backend.app.services.aa_service import AccountAggregatorService

        uid            = uuid.UUID(user_id)
        fetched_count  = 0
        error_count    = 0

        async with AsyncSessionLocal() as db:
            svc             = AccountAggregatorService(db)
            consent_repo    = AAConsentRepository(db)
            active_consents = await consent_repo.list_for_user(uid, status=ConsentStatus.ACTIVE)

            for consent in active_consents:
                try:
                    records = await svc.initiate_fetch(user_id=uid, consent_pk=consent.id)
                    fetched_count += len(records)
                except Exception as exc:
                    error_count += 1
                    logger.error("AA fetch failed: user=%s consent=%s error=%s", user_id, consent.id, exc)

            await db.commit()

        return {
            "user_id": user_id,
            "consents_processed": len(active_consents),
            "fetch_records_created": fetched_count,
            "errors": error_count,
        }

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error("refresh_aa_data_for_user failed for %s: %s", user_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(name="backend.app.workers.aa_workers.refresh_all_active_consents", bind=True)
def refresh_all_active_consents(self) -> dict:
    """Periodic: enqueue per-user refresh for all users with active consents."""
    async def _run():
        from sqlalchemy import select
        from backend.app.db.database import AsyncSessionLocal
        from backend.app.models.aa_consent import AAConsent, ConsentStatus

        async with AsyncSessionLocal() as db:
            stmt     = select(AAConsent.user_id).where(AAConsent.status == ConsentStatus.ACTIVE).distinct()
            result   = await db.execute(stmt)
            user_ids = [str(row[0]) for row in result.fetchall()]
        return user_ids

    user_ids = _run_async(_run())
    for uid in user_ids:
        refresh_aa_data_for_user.delay(uid)
    logger.info("Enqueued AA refresh for %d users", len(user_ids))
    return {"users_enqueued": len(user_ids)}


@celery_app.task(
    name="backend.app.workers.aa_workers.recompute_networth_for_user",
    bind=True, max_retries=2, default_retry_delay=60,
)
def recompute_networth_for_user(self, user_id: str) -> dict:
    """Recompute and snapshot net worth for a user."""
    async def _run():
        from backend.app.db.database import AsyncSessionLocal
        from backend.app.services.asset_service import NetWorthService

        uid = uuid.UUID(user_id)
        async with AsyncSessionLocal() as db:
            svc    = NetWorthService(db)
            result = await svc.recompute(uid)
            await db.commit()
            return {
                "user_id":     user_id,
                "snapshot_id": str(result.snapshot_id),
                "net_worth":   float(result.net_worth),
                "computed_at": result.computed_at.isoformat(),
            }

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error("recompute_networth_for_user failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(name="backend.app.workers.aa_workers.expire_stale_consents")
def expire_stale_consents() -> dict:
    """Periodic: mark consents past their expiry date as EXPIRED."""
    async def _run():
        from sqlalchemy import update
        from backend.app.db.database import AsyncSessionLocal
        from backend.app.models.aa_consent import AAConsent, ConsentStatus

        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as db:
            stmt = (
                update(AAConsent)
                .where(AAConsent.status == ConsentStatus.ACTIVE)
                .where(AAConsent.consent_expiry < now)
                .values(status=ConsentStatus.EXPIRED)
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount

    expired_count = _run_async(_run())
    logger.info("Expired %d stale AA consents", expired_count)
    return {"expired_count": expired_count}


def trigger_full_refresh(user_id: str) -> None:
    """Convenience: chain AA refresh → net worth recompute."""
    from celery import chain
    chain(
        refresh_aa_data_for_user.s(user_id),
        recompute_networth_for_user.si(user_id),
    ).delay()
