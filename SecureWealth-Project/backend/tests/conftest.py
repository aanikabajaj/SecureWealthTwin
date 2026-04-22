"""
SecureWealth Twin — pytest fixtures.

Uses SQLite in-memory for speed. Each test gets a fresh DB and HTTP client.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.db.database import Base, get_db
from backend.app.main import app

# ── In-memory SQLite test engine ──────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ── Session-scoped event loop ─────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── DB fixture: create tables once per session, rollback per test ─────────────

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    import backend.app.models  # noqa: ensure all models are registered
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


# ── Override FastAPI's get_db with the test session ───────────────────────────

@pytest_asyncio.fixture
async def client(db: AsyncSession):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Pre-registered test user helpers ──────────────────────────────────────────

TEST_EMAIL    = "test@securewealth.in"
TEST_PASSWORD = "TestPass123!"


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Register + login, return Authorization headers."""
    # Register
    await client.post("/api/v1/auth/register", json={
        "email":     TEST_EMAIL,
        "password":  TEST_PASSWORD,
        "full_name": "Test User",
    })
    # Login
    resp = await client.post("/api/v1/auth/login", json={
        "email":    TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
