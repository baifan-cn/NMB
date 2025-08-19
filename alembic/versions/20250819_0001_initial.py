"""
Initial schema

Revision ID: 20250819_0001
Revises: 
Create Date: 2025-08-19 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20250819_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("real_name", sa.String(length=100), nullable=True),
        sa.Column("status", sa.Enum("active", "inactive", "banned", name="user_status"), nullable=False, server_default="active"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("idx_users_status", "users", ["status"], unique=False)
    op.create_index("idx_users_last_login_at", "users", ["last_login_at"], unique=False)

    # member_tiers
    op.create_table(
        "member_tiers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("price_monthly", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_yearly", sa.Numeric(10, 2), nullable=True),
        sa.Column("max_downloads_per_month", sa.Integer(), nullable=True),
        sa.Column("access_history_days", sa.Integer(), nullable=True),
        sa.Column("can_view_current_week", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("level", name="uq_member_tiers_level"),
    )

    # user_memberships
    op.create_table(
        "user_memberships",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tier_id", sa.Integer(), sa.ForeignKey("member_tiers.id"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.Enum("active", "expired", "cancelled", name="membership_status"), nullable=False, server_default="active"),
        sa.Column("payment_id", sa.BigInteger(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_user_memberships_user_id", "user_memberships", ["user_id"], unique=False)

    # magazines
    op.create_table(
        "magazines",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("issue_number", sa.String(length=50), nullable=False),
        sa.Column("publish_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_image_url", sa.String(length=500), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("encrypted_key", sa.String(length=255), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )
    op.create_index("idx_publish_date", "magazines", ["publish_date"], unique=False)
    op.create_index("idx_issue_number", "magazines", ["issue_number"], unique=False)

    # magazine_categories
    op.create_table(
        "magazine_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("magazine_categories.id"), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("magazine_categories.id"), nullable=False),
        sa.Column("frequency", sa.Enum("daily", "weekly", "monthly", name="subscription_frequency"), nullable=False),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_send_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Enum("active", "paused", "cancelled", name="subscription_status"), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )
    op.create_index("idx_next_send", "subscriptions", ["next_send_at", "status"], unique=False)

    # payments
    op.create_table(
        "payments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tier_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="CNY"),
        sa.Column("payment_method", sa.Enum("alipay", "wechat", "bank_card", name="payment_method"), nullable=False),
        sa.Column("status", sa.Enum("pending", "success", "failed", "cancelled", "refunded", name="payment_status"), nullable=False, server_default="pending"),
        sa.Column("transaction_id", sa.String(length=100), nullable=True),
        sa.Column("external_transaction_id", sa.String(length=100), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"], unique=False)

    # downloads
    op.create_table(
        "downloads",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("magazine_id", sa.BigInteger(), sa.ForeignKey("magazines.id"), nullable=False),
        sa.Column("download_time", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("download_duration", sa.Integer(), nullable=True),
        sa.Column("status", sa.Enum("success", "failed", "cancelled", name="download_status"), nullable=False, server_default="success"),
    )
    op.create_index("ix_downloads_user_id", "downloads", ["user_id"], unique=False)
    op.create_index("ix_downloads_magazine_id", "downloads", ["magazine_id"], unique=False)

    # social_accounts
    op.create_table(
        "social_accounts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("provider", sa.Enum("wechat", "weibo", "douyin", name="social_provider"), nullable=False),
        sa.Column("provider_user_id", sa.String(length=191), nullable=False),
        sa.Column("union_id", sa.String(length=191), nullable=True),
        sa.Column("access_token", sa.String(length=1024), nullable=True),
        sa.Column("refresh_token", sa.String(length=1024), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.String(length=255), nullable=True),
        sa.Column("nickname_snapshot", sa.String(length=255), nullable=True),
        sa.Column("avatar_snapshot", sa.String(length=500), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_social_provider_user"),
    )
    op.create_index("ix_social_user_id", "social_accounts", ["user_id"], unique=False)
    op.create_index("idx_social_union_id", "social_accounts", ["union_id"], unique=False)

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=True),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("idx_social_union_id", table_name="social_accounts")
    op.drop_index("ix_social_user_id", table_name="social_accounts")
    op.drop_table("social_accounts")

    op.drop_index("ix_downloads_magazine_id", table_name="downloads")
    op.drop_index("ix_downloads_user_id", table_name="downloads")
    op.drop_table("downloads")

    op.drop_index("ix_payments_user_id", table_name="payments")
    op.drop_table("payments")

    op.drop_index("idx_next_send", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_table("magazine_categories")

    op.drop_index("idx_issue_number", table_name="magazines")
    op.drop_index("idx_publish_date", table_name="magazines")
    op.drop_table("magazines")

    op.drop_index("ix_user_memberships_user_id", table_name="user_memberships")
    op.drop_table("user_memberships")

    op.drop_table("member_tiers")

    op.drop_index("idx_users_last_login_at", table_name="users")
    op.drop_index("idx_users_status", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
