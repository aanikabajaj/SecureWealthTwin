"""
SecureWealth Twin — Generic Async Repository Base.
"""

from __future__ import annotations

import uuid
from typing import Generic, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import Base

ModelT = TypeVar("ModelT", bound=Base)  # type: ignore[type-arg]


class BaseRepository(Generic[ModelT]):
    """
    Thin CRUD base. Subclasses set `model = MyModel` and inherit
    create / get_by_id / delete without boilerplate.
    """

    model: Type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, pk: uuid.UUID) -> ModelT | None:
        stmt = select(self.model).where(self.model.id == pk)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.flush()

    async def list_all(self) -> list[ModelT]:
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
