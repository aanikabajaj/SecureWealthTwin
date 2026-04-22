"""
SecureWealth Twin — FastAPI Application Entry Point.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import get_settings

settings = get_settings()
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("securewealth")


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import all models so Alembic / create_all can discover them
    import backend.app.models  # noqa: F401  (registers all ORM classes)

    if settings.USE_SQLITE or settings.ENVIRONMENT == "development":
        from backend.app.db.database import create_all_tables
        await create_all_tables()
        logger.info("DB tables ensured (dev mode)")

    logger.info("SecureWealth Twin API starting — env=%s", settings.ENVIRONMENT)
    yield
    logger.info("SecureWealth Twin API shutting down")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SecureWealth Twin API",
    description=(
        "AI-powered wealth management backend.\n\n"
        "Features:\n"
        "- **Auth**: JWT register/login/refresh\n"
        "- **Account Aggregator**: RBI-compliant consent + FI data fetch (Finvu/OneMoney)\n"
        "- **Physical Assets**: Property, gold, vehicles, jewellery, art, business\n"
        "- **Net Worth Engine**: Full aggregation across all asset classes\n"
        "- **Blockchain Audit**: Immutable ledger for transaction security\n"
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s %s — %s", request.method, request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again."},
    )


# ── Routers ───────────────────────────────────────────────────────────────────

from backend.app.api.v1.routers import auth        as auth_router
from backend.app.api.v1.routers import aggregator  as aggregator_router
from backend.app.api.v1.routers import assets      as assets_router
from backend.app.api.v1.routers import networth    as networth_router
from backend.app.api.v1.routers import audit       as audit_router
from backend.app.api.v1.routers import advisor     as advisor_router
from backend.app.api.v1.routers import simulator   as simulator_router
from backend.app.api.v1.routers import chat        as chat_router
from backend.app.api.v1.routers import market      as market_router

app.include_router(auth_router.router,        prefix="/api/v1/auth",        tags=["Auth"])
app.include_router(aggregator_router.router,  prefix="/api/v1/aggregator",  tags=["Account Aggregator"])
app.include_router(assets_router.router,      prefix="/api/v1/assets",      tags=["Physical Assets"])
app.include_router(networth_router.router,    prefix="/api/v1/networth",    tags=["Net Worth"])
app.include_router(audit_router.router,       prefix="/api/v1/audit",       tags=["Blockchain Audit"])
app.include_router(advisor_router.router,     prefix="/api/v1/advisor",     tags=["Wealth Advisor"])
app.include_router(simulator_router.router,   prefix="/api/v1/simulator",   tags=["Scenario Simulator"])
app.include_router(chat_router.router,        prefix="/api/v1/chat",        tags=["AI Chat Advisor"])
app.include_router(market_router.router,      prefix="/api/v1/market",      tags=["Market Data"])


# ── Health & root ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "SecureWealth Twin API",
        "version": settings.APP_VERSION,
        "status":  "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
