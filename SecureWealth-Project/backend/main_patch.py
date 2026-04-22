"""
SecureWealth Twin — Updated main.py router registration block.

INSTRUCTIONS: In your existing backend/app/main.py, find the
"── Routers ──" section and REPLACE it with the block below.
Everything else (lifespan, middleware, health, metrics) stays the same.
"""

# ── Routers ──────────────────────────────────────────────────────────────────
#
# Paste this entire block replacing the existing router imports + includes:
#
# from backend.app.api.v1.routers import auth as auth_router
# from backend.app.api.v1.routers import transactions as txn_router
# from backend.app.api.v1.routers import wealth as wealth_router
# from backend.app.api.v1.routers import risk as risk_router
# from backend.app.api.v1.routers import aggregator as aggregator_router   # NEW
# from backend.app.api.v1.routers import assets as assets_router           # NEW
# from backend.app.api.v1.routers import networth as networth_router       # NEW
#
# app.include_router(auth_router.router,        prefix="/api/v1/auth",        tags=["Auth"])
# app.include_router(txn_router.router,         prefix="/api/v1/transactions", tags=["Transactions"])
# app.include_router(wealth_router.router,      prefix="/api/v1/wealth",       tags=["Wealth Twin"])
# app.include_router(risk_router.router,        prefix="/api/v1/risk",         tags=["Risk Engine"])
# app.include_router(aggregator_router.router,  prefix="/api/v1/aggregator",   tags=["Account Aggregator"])  # NEW
# app.include_router(assets_router.router,      prefix="/api/v1/assets",       tags=["Physical Assets"])     # NEW
# app.include_router(networth_router.router,    prefix="/api/v1/networth",     tags=["Net Worth"])           # NEW

ROUTER_REGISTRATION_PATCH = """
    from backend.app.api.v1.routers import auth as auth_router
    from backend.app.api.v1.routers import transactions as txn_router
    from backend.app.api.v1.routers import wealth as wealth_router
    from backend.app.api.v1.routers import risk as risk_router
    from backend.app.api.v1.routers import aggregator as aggregator_router
    from backend.app.api.v1.routers import assets as assets_router
    from backend.app.api.v1.routers import networth as networth_router

    app.include_router(auth_router.router,       prefix="/api/v1/auth",        tags=["Auth"])
    app.include_router(txn_router.router,        prefix="/api/v1/transactions", tags=["Transactions"])
    app.include_router(wealth_router.router,     prefix="/api/v1/wealth",       tags=["Wealth Twin"])
    app.include_router(risk_router.router,       prefix="/api/v1/risk",         tags=["Risk Engine"])
    app.include_router(aggregator_router.router, prefix="/api/v1/aggregator",   tags=["Account Aggregator"])
    app.include_router(assets_router.router,     prefix="/api/v1/assets",       tags=["Physical Assets"])
    app.include_router(networth_router.router,   prefix="/api/v1/networth",     tags=["Net Worth"])
"""
