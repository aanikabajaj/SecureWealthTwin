"""
SecureWealth Twin — Account Aggregator Repository.

All DB queries for AAConsent, AALinkedAccount, AAFetchedData.
Inherits generic CRUD from BaseRepository.
"""

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.repository_base import BaseRepository
from backend.app.models.aa_consent import (
    AAConsent,
    AAFetchedData,
    AALinkedAccount,
    ConsentStatus,
)


class AAConsentRepository(BaseRepository[AAConsent]):
    model = AAConsent

    async def get_by_handle(self, handle: str) -> AAConsent | None:
        stmt = select(AAConsent).where(AAConsent.consent_handle == handle)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_consent_id(self, consent_id: str) -> AAConsent | None:
        stmt = select(AAConsent).where(AAConsent.consent_id == consent_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        status: ConsentStatus | None = None,
    ) -> list[AAConsent]:
        stmt = select(AAConsent).where(AAConsent.user_id == user_id)
        if status:
            stmt = stmt.where(AAConsent.status == status)
        stmt = stmt.order_by(AAConsent.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        consent_id_pk: uuid.UUID,
        status: ConsentStatus,
        consent_id_str: str | None = None,
        reason: str | None = None,
        raw_response: dict | None = None,
    ) -> None:
        values: dict = {"status": status, "updated_at": datetime.utcnow()}
        if consent_id_str:
            values["consent_id"] = consent_id_str
        if reason:
            values["status_reason"] = reason
        if raw_response:
            values["raw_response"] = raw_response
        stmt = (
            update(AAConsent)
            .where(AAConsent.id == consent_id_pk)
            .values(**values)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def count_active_for_user(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(AAConsent)
            .where(AAConsent.user_id == user_id)
            .where(AAConsent.status == ConsentStatus.ACTIVE)
        )
        result = await self.session.execute(stmt)
        return len(result.scalars().all())


class AALinkedAccountRepository(BaseRepository[AALinkedAccount]):
    model = AALinkedAccount

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        active_only: bool = True,
    ) -> list[AALinkedAccount]:
        stmt = select(AALinkedAccount).where(AALinkedAccount.user_id == user_id)
        if active_only:
            stmt = stmt.where(AALinkedAccount.is_active == True)  # noqa: E712
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_consent(self, consent_id: uuid.UUID) -> list[AALinkedAccount]:
        stmt = (
            select(AALinkedAccount)
            .where(AALinkedAccount.consent_id == consent_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_account(
        self,
        user_id: uuid.UUID,
        consent_id: uuid.UUID,
        fip_id: str,
        account_ref: str,
        defaults: dict,
    ) -> AALinkedAccount:
        """Insert or update a linked account based on FIP + account_ref."""
        stmt = (
            select(AALinkedAccount)
            .where(AALinkedAccount.user_id == user_id)
            .where(AALinkedAccount.fip_id == fip_id)
            .where(AALinkedAccount.account_ref_number == account_ref)
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            for k, v in defaults.items():
                setattr(existing, k, v)
            await self.session.flush()
            await self.session.refresh(existing)
            return existing

        account = AALinkedAccount(
            user_id=user_id,
            consent_id=consent_id,
            fip_id=fip_id,
            account_ref_number=account_ref,
            **defaults,
        )
        return await self.create(account)

    async def update_balance(
        self,
        account_id: uuid.UUID,
        balance: float,
    ) -> None:
        stmt = (
            update(AALinkedAccount)
            .where(AALinkedAccount.id == account_id)
            .values(
                current_balance=balance,
                last_fetched_at=datetime.utcnow(),
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def total_balance_for_user(self, user_id: uuid.UUID) -> float:
        accounts = await self.list_for_user(user_id, active_only=True)
        return sum(float(a.current_balance) for a in accounts)


class AAFetchedDataRepository(BaseRepository[AAFetchedData]):
    model = AAFetchedData

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        fi_type: str | None = None,
    ) -> list[AAFetchedData]:
        stmt = (
            select(AAFetchedData)
            .where(AAFetchedData.user_id == user_id)
            .order_by(AAFetchedData.created_at.desc())
        )
        if fi_type:
            stmt = stmt.where(AAFetchedData.fi_type == fi_type)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_session(self, session_id: str) -> AAFetchedData | None:
        stmt = select(AAFetchedData).where(AAFetchedData.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
