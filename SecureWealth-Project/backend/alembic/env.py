"""
SecureWealth Twin — Alembic Async Environment.

Uses the app's own Settings so DATABASE_URL comes from .env (no duplication).
Supports async migrations with asyncpg.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# ── Load app config & models ───────────────────────────────────────────────────
from backend.app.config import get_settings
from backend.app.db.database import Base

# Import ALL models so Alembic can detect every table
import backend.app.models  # noqa: F401 — registers all ORM classes with Base

settings = get_settings()
config   = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ── Offline migrations (SQL script generation) ────────────────────────────────

def run_migrations_offline() -> None:
    """Generate SQL without connecting to the DB."""
    url = settings.effective_db_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations (actual DB connection) ──────────────────────────────────

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine."""
    connectable = create_async_engine(settings.effective_db_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ── Entry point ───────────────────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
