# SecureWealth Twin — Feature Addition Guide
## Features: AA Integration + Physical Assets + Full Net Worth

---

## What Was Built

### 3 New Features, 12 New Files

```
backend/app/
├── models/
│   ├── aa_consent.py          ← NEW: AAConsent, AALinkedAccount, AAFetchedData
│   ├── physical_asset.py      ← NEW: PhysicalAsset (property, gold, vehicle…)
│   ├── networth_snapshot.py   ← NEW: Immutable net-worth point-in-time record
│   └── __init__.py            ← REPLACE: adds new models to registry
│
├── schemas/
│   ├── aa_schemas.py          ← NEW: Pydantic request/response for AA endpoints
│   └── asset_schemas.py       ← NEW: Pydantic for assets + net-worth endpoints
│
├── repositories/
│   ├── aa_repository.py       ← NEW: DB queries for AA models
│   └── asset_repository.py    ← NEW: DB queries for assets + snapshots
│
├── services/
│   ├── aa_service.py          ← NEW: AA consent lifecycle + fetch + financial picture
│   └── asset_service.py       ← NEW: PhysicalAssetService + NetWorthService
│
├── api/v1/routers/
│   ├── aggregator.py          ← NEW: /api/v1/aggregator/* routes
│   ├── assets.py              ← NEW: /api/v1/assets/* routes
│   └── networth.py            ← NEW: /api/v1/networth/* routes
│
└── alembic_migrations/
    └── 0002_aa_assets_networth.py  ← NEW: DB migration for 5 new tables
```

---

## Integration Steps

### Step 1 — Copy new files into your project

Copy all files above into the corresponding folders in `backend/app/`.

### Step 2 — Replace models/__init__.py

Replace `backend/app/models/__init__.py` with the new one provided.

### Step 3 — Patch User model relationships

In `backend/app/models/user.py`, add these relationships to the `User` class:

```python
aa_consents = relationship("AAConsent", back_populates="user", lazy="selectin")
aa_linked_accounts = relationship("AALinkedAccount", back_populates="user", lazy="selectin")
aa_fetched_data = relationship("AAFetchedData", back_populates="user", lazy="selectin")
physical_assets = relationship("PhysicalAsset", back_populates="user", lazy="selectin")
networth_snapshots = relationship("NetWorthSnapshot", back_populates="user", lazy="selectin")
```

### Step 4 — Register new routers in main.py

In `backend/app/main.py`, add to the routers section:

```python
from backend.app.api.v1.routers import aggregator as aggregator_router
from backend.app.api.v1.routers import assets as assets_router
from backend.app.api.v1.routers import networth as networth_router

app.include_router(aggregator_router.router, prefix="/api/v1/aggregator", tags=["Account Aggregator"])
app.include_router(assets_router.router,     prefix="/api/v1/assets",     tags=["Physical Assets"])
app.include_router(networth_router.router,   prefix="/api/v1/networth",   tags=["Net Worth"])
```

### Step 5 — Run Alembic migration

```bash
# Update down_revision in 0002_aa_assets_networth.py to match your last migration
alembic upgrade head
```

### Step 6 — Add env variables (if production AA)

```env
# .env — only needed for live AA (sandbox works without these)
FERNET_KEY=<your-fernet-key>          # already in config.py
AA_FINVU_API_KEY=<your-finvu-key>     # add to config.py if needed
AA_WEBHOOK_SECRET=<hmac-secret>
```

---

## API Reference

### Feature 1: Account Aggregator

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/aggregator/consents` | Raise consent with AA (Finvu/OneMoney) |
| GET | `/api/v1/aggregator/consents` | List all consents |
| DELETE | `/api/v1/aggregator/consents/{id}` | Revoke consent |
| POST | `/api/v1/aggregator/fetch` | Trigger FI data pull from banks |
| GET | `/api/v1/aggregator/accounts` | View all linked bank accounts |
| GET | `/api/v1/aggregator/financial-picture` | Full cross-bank financial picture |
| POST | `/api/v1/aggregator/webhook/consent-status` | AA webhook (HMAC verified) |

### Feature 2: Physical Assets

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/assets` | Add property / gold / vehicle / jewellery |
| GET | `/api/v1/assets` | List all assets (filter by category) |
| GET | `/api/v1/assets/summary` | Totals grouped by category |
| GET | `/api/v1/assets/{id}` | Get single asset |
| PATCH | `/api/v1/assets/{id}` | Update valuation (creates history snapshot) |
| DELETE | `/api/v1/assets/{id}` | Soft-retire asset |

### Feature 3: Full Net Worth

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/networth` | Latest net-worth snapshot |
| POST | `/api/v1/networth/recompute` | Trigger full recomputation |
| GET | `/api/v1/networth/history` | Time-series of net-worth snapshots |

---

## Net Worth Formula

```
gross_assets      = financial_assets (WealthProfile)
                  + aa_assets        (AALinkedAccount balances)
                  + physical_assets  (PhysicalAsset effective values)

total_liabilities = sum of outstanding_loan on physical assets

net_worth         = gross_assets - total_liabilities
```

---

## Sandbox Mode

All AA calls run against sandbox mock responses when `ENVIRONMENT != production`.
No live AA credentials needed for development. Mock data returns:
- HDFC-FIP account with ₹3,25,000 balance
- SBI-FIP account with ₹98,500 balance

---

## Security Notes

- AA raw payloads are **Fernet-encrypted** at rest (`encrypted_payload` column)
- AA webhook uses **HMAC-SHA256** signature verification
- All endpoints require **JWT auth** via existing `get_current_user` dependency
- Audit trail integrates with existing **hash-chained AuditLog** model
- Asset ownership scoping: every DB query filters by `user_id`
