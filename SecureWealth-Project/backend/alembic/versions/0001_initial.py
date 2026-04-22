"""
SecureWealth Twin — Initial Migration.
Creates all tables from scratch.

Revision ID: 0001_initial
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision      = "0001_initial"
down_revision = None
branch_labels = None
depends_on    = None


def upgrade() -> None:

    # ── users ──────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",              sa.Uuid(),     nullable=False),
        sa.Column("email",           sa.String(255), nullable=False),
        sa.Column("phone",           sa.String(20),  nullable=True),
        sa.Column("full_name",       sa.String(255), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role",            sa.Enum("customer","advisor","admin", name="user_role", native_enum=False), nullable=False, server_default="customer"),
        sa.Column("is_active",       sa.Boolean(),  nullable=False, server_default="true"),
        sa.Column("is_verified",     sa.Boolean(),  nullable=False, server_default="false"),
        sa.Column("kyc_status",      sa.String(32), nullable=False, server_default="pending"),
        sa.Column("aa_vua",          sa.String(255), nullable=True),
        sa.Column("created_at",      sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",      sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── wealth_profiles ────────────────────────────────────────────
    op.create_table(
        "wealth_profiles",
        sa.Column("id",               sa.Uuid(),          nullable=False),
        sa.Column("user_id",          sa.Uuid(),          nullable=False),
        sa.Column("total_savings",    sa.Numeric(18, 2),  nullable=False, server_default="0"),
        sa.Column("total_investments",sa.Numeric(18, 2),  nullable=False, server_default="0"),
        sa.Column("total_liabilities",sa.Numeric(18, 2),  nullable=False, server_default="0"),
        sa.Column("net_worth",        sa.Numeric(18, 2),  nullable=False, server_default="0"),
        sa.Column("monthly_income",   sa.Numeric(18, 2),  nullable=False, server_default="0"),
        sa.Column("monthly_expenses", sa.Numeric(18, 2),  nullable=False, server_default="0"),
        sa.Column("risk_tolerance",   sa.Enum("conservative","moderate","aggressive", name="risk_tolerance", native_enum=False), nullable=False, server_default="moderate"),
        sa.Column("investment_goals", sa.Text(),          nullable=True),
        sa.Column("notes",            sa.Text(),          nullable=True),
        sa.Column("created_at",       sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",       sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
    )

    # ── transactions ───────────────────────────────────────────────
    op.create_table(
        "transactions",
        sa.Column("id",               sa.Uuid(),         nullable=False),
        sa.Column("user_id",          sa.Uuid(),         nullable=False),
        sa.Column("amount",           sa.Numeric(18, 2), nullable=False),
        sa.Column("currency",         sa.String(3),      nullable=False, server_default="INR"),
        sa.Column("description",      sa.String(512),    nullable=True),
        sa.Column("category",         sa.String(64),     nullable=True),
        sa.Column("reference",        sa.String(128),    nullable=True),
        sa.Column("transaction_type", sa.Enum("credit","debit", name="transaction_type", native_enum=False), nullable=False),
        sa.Column("status",           sa.Enum("pending","completed","failed","reversed", name="transaction_status", native_enum=False), nullable=False, server_default="completed"),
        sa.Column("transacted_at",    sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at",       sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])

    # ── audit_logs ─────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id",          sa.Uuid(),    nullable=False),
        sa.Column("user_id",     sa.Uuid(),    nullable=True),
        sa.Column("action",      sa.String(128), nullable=False),
        sa.Column("resource",    sa.String(128), nullable=True),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("detail",      sa.JSON(),    nullable=True),
        sa.Column("ip_address",  sa.String(45), nullable=True),
        sa.Column("user_agent",  sa.Text(),    nullable=True),
        sa.Column("prev_hash",   sa.String(64), nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])

    # ── aa_consents ────────────────────────────────────────────────
    op.create_table(
        "aa_consents",
        sa.Column("id",             sa.Uuid(),     nullable=False),
        sa.Column("user_id",        sa.Uuid(),     nullable=False),
        sa.Column("aa_id",          sa.String(64), nullable=False),
        sa.Column("consent_handle", sa.String(255), nullable=True, unique=True),
        sa.Column("consent_id",     sa.String(255), nullable=True, unique=True),
        sa.Column("purpose_code",   sa.String(32), nullable=False, server_default="03"),
        sa.Column("fi_types",       sa.JSON(),     nullable=True),
        sa.Column("date_range_from",sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_range_to",  sa.DateTime(timezone=True), nullable=True),
        sa.Column("consent_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetch_frequency",sa.String(32), nullable=False, server_default="MONTHLY"),
        sa.Column("status",         sa.Enum("pending","active","paused","revoked","expired","failed", name="consent_status", native_enum=False), nullable=False, server_default="pending"),
        sa.Column("status_reason",  sa.Text(),     nullable=True),
        sa.Column("raw_response",   sa.JSON(),     nullable=True),
        sa.Column("created_at",     sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",     sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_aa_consent_user_status",  "aa_consents", ["user_id", "status"])
    op.create_index("ix_aa_consents_user_id",     "aa_consents", ["user_id"])

    # ── aa_linked_accounts ─────────────────────────────────────────
    op.create_table(
        "aa_linked_accounts",
        sa.Column("id",                    sa.Uuid(),      nullable=False),
        sa.Column("user_id",               sa.Uuid(),      nullable=False),
        sa.Column("consent_id",            sa.Uuid(),      nullable=False),
        sa.Column("fip_id",                sa.String(64),  nullable=False),
        sa.Column("fip_name",              sa.String(128), nullable=False),
        sa.Column("account_ref_number",    sa.String(128), nullable=False),
        sa.Column("account_type",          sa.Enum("savings","current","recurring","fixed_deposit","mutual_fund","equity","nps","insurance","other", name="account_type", native_enum=False), nullable=False, server_default="savings"),
        sa.Column("masked_account_number", sa.String(32),  nullable=True),
        sa.Column("ifsc",                  sa.String(11),  nullable=True),
        sa.Column("current_balance",       sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("currency",              sa.String(3),   nullable=False, server_default="INR"),
        sa.Column("is_active",             sa.Boolean(),   nullable=False, server_default="true"),
        sa.Column("last_fetched_at",       sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at",            sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",            sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"],    ["users.id"],       ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["consent_id"], ["aa_consents.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_aa_linked_user_fip",       "aa_linked_accounts", ["user_id", "fip_id"])
    op.create_index("ix_aa_linked_accounts_user_id","aa_linked_accounts", ["user_id"])

    # ── aa_fetched_data ────────────────────────────────────────────
    op.create_table(
        "aa_fetched_data",
        sa.Column("id",                sa.Uuid(),     nullable=False),
        sa.Column("user_id",           sa.Uuid(),     nullable=False),
        sa.Column("consent_id",        sa.Uuid(),     nullable=False),
        sa.Column("linked_account_id", sa.Uuid(),     nullable=True),
        sa.Column("session_id",        sa.String(255),nullable=False),
        sa.Column("fi_type",           sa.String(32), nullable=False),
        sa.Column("status",            sa.Enum("initiated","in_progress","success","partial","failed", name="fetch_status", native_enum=False), nullable=False, server_default="initiated"),
        sa.Column("encrypted_payload", sa.Text(),     nullable=True),
        sa.Column("summary",           sa.JSON(),     nullable=True),
        sa.Column("fetch_error",       sa.Text(),     nullable=True),
        sa.Column("fetched_at",        sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at",        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"],           ["users.id"],              ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["consent_id"],        ["aa_consents.id"],        ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["linked_account_id"], ["aa_linked_accounts.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_aa_fetched_user_fi",      "aa_fetched_data", ["user_id", "fi_type"])
    op.create_index("ix_aa_fetched_session",      "aa_fetched_data", ["session_id"])
    op.create_index("ix_aa_fetched_data_user_id", "aa_fetched_data", ["user_id"])

    # ── physical_assets ────────────────────────────────────────────
    op.create_table(
        "physical_assets",
        sa.Column("id",                   sa.Uuid(),         nullable=False),
        sa.Column("user_id",              sa.Uuid(),         nullable=False),
        sa.Column("category",             sa.Enum("real_estate","gold","vehicle","jewellery","art_collectible","business","other", name="asset_category", native_enum=False), nullable=False),
        sa.Column("name",                 sa.String(255),    nullable=False),
        sa.Column("description",          sa.Text(),         nullable=True),
        sa.Column("current_value",        sa.Numeric(18, 2), nullable=False),
        sa.Column("purchase_value",       sa.Numeric(18, 2), nullable=True),
        sa.Column("purchase_date",        sa.Date(),         nullable=True),
        sa.Column("valuation_date",       sa.Date(),         nullable=False),
        sa.Column("valuation_method",     sa.Enum("self_declared","market_price","govt_circle_rate","professional", name="valuation_method", native_enum=False), nullable=False, server_default="self_declared"),
        sa.Column("outstanding_loan",     sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("ownership_type",       sa.Enum("sole","joint","inherited","trust", name="ownership_type", native_enum=False), nullable=False, server_default="sole"),
        sa.Column("ownership_percentage", sa.Numeric(5, 2),  nullable=False, server_default="100.00"),
        sa.Column("metadata_json",        sa.JSON(),         nullable=True),
        sa.Column("document_urls",        sa.JSON(),         nullable=True),
        sa.Column("is_current",           sa.Boolean(),      nullable=False, server_default="true"),
        sa.Column("include_in_networth",  sa.Boolean(),      nullable=False, server_default="true"),
        sa.Column("created_at",           sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",           sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_asset_user_category",    "physical_assets", ["user_id", "category"])
    op.create_index("ix_asset_user_current",     "physical_assets", ["user_id", "is_current"])
    op.create_index("ix_physical_assets_user_id","physical_assets", ["user_id"])

    # ── networth_snapshots ─────────────────────────────────────────
    op.create_table(
        "networth_snapshots",
        sa.Column("id",               sa.Uuid(),         nullable=False),
        sa.Column("user_id",          sa.Uuid(),         nullable=False),
        sa.Column("financial_assets", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("aa_assets",        sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("physical_assets",  sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("total_liabilities",sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("gross_assets",     sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("net_worth",        sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("breakdown",        sa.JSON(),         nullable=True),
        sa.Column("computed_at",      sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_networth_user_time",        "networth_snapshots", ["user_id", "computed_at"])
    op.create_index("ix_networth_snapshots_user_id","networth_snapshots", ["user_id"])


def downgrade() -> None:
    op.drop_table("networth_snapshots")
    op.drop_table("physical_assets")
    op.drop_table("aa_fetched_data")
    op.drop_table("aa_linked_accounts")
    op.drop_table("aa_consents")
    op.drop_table("audit_logs")
    op.drop_table("transactions")
    op.drop_table("wealth_profiles")
    op.drop_table("users")
    for t in ["consent_status","fetch_status","account_type","asset_category",
              "valuation_method","ownership_type","user_role","risk_tolerance",
              "transaction_type","transaction_status"]:
        op.execute(f"DROP TYPE IF EXISTS {t}")
