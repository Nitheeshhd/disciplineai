"""initial enterprise schema

Revision ID: 20260302_0001
Revises:
Create Date: 2026-03-02 16:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260302_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_roles_name_not_deleted", "roles", ["name", "is_deleted"], unique=False)
    op.create_index(op.f("ix_roles_deleted_at"), "roles", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_roles_is_deleted"), "roles", ["is_deleted"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=True),
        sa.Column("last_name", sa.String(length=120), nullable=True),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("locale", sa.String(length=16), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("is_premium", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("length(email) >= 5", name="ck_users_email_len"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("telegram_user_id"),
    )
    op.create_index("ix_users_active_deleted", "users", ["is_active", "is_deleted"], unique=False)
    op.create_index(op.f("ix_users_deleted_at"), "users", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_gender"), "users", ["gender"], unique=False)
    op.create_index(op.f("ix_users_is_deleted"), "users", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_users_telegram_user_id"), "users", ["telegram_user_id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=False)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )
    op.create_index(op.f("ix_user_roles_role_id"), "user_roles", ["role_id"], unique=False)
    op.create_index(op.f("ix_user_roles_user_id"), "user_roles", ["user_id"], unique=False)

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("refresh_token_jti", sa.String(length=64), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("refresh_token_jti"),
    )
    op.create_index("ix_sessions_user_expires", "sessions", ["user_id", "expires_at"], unique=False)
    op.create_index("ix_sessions_revoked", "sessions", ["revoked_at"], unique=False)
    op.create_index(op.f("ix_sessions_deleted_at"), "sessions", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_sessions_expires_at"), "sessions", ["expires_at"], unique=False)
    op.create_index(op.f("ix_sessions_is_deleted"), "sessions", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_sessions_refresh_token_jti"), "sessions", ["refresh_token_jti"], unique=False)
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("telegram_chat_id", sa.Integer(), nullable=False),
        sa.Column("telegram_message_id", sa.Integer(), nullable=False),
        sa.Column("message_type", sa.String(length=40), nullable=False),
        sa.Column("message_text", sa.String(length=2000), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("message_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_user_date_type", "messages", ["user_id", "message_date", "message_type"], unique=False)
    op.create_index("ix_messages_chat_msgid", "messages", ["telegram_chat_id", "telegram_message_id"], unique=True)
    op.create_index(op.f("ix_messages_deleted_at"), "messages", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_messages_is_deleted"), "messages", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_messages_message_date"), "messages", ["message_date"], unique=False)
    op.create_index(op.f("ix_messages_message_type"), "messages", ["message_type"], unique=False)
    op.create_index(op.f("ix_messages_telegram_chat_id"), "messages", ["telegram_chat_id"], unique=False)
    op.create_index(op.f("ix_messages_telegram_message_id"), "messages", ["telegram_message_id"], unique=False)
    op.create_index(op.f("ix_messages_user_id"), "messages", ["user_id"], unique=False)

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("transaction_ref", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("payment_status", sa.String(length=30), nullable=False),
        sa.Column("paid_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_ref"),
    )
    op.create_index("ix_payments_user_paid_date", "payments", ["user_id", "paid_date"], unique=False)
    op.create_index("ix_payments_status_date", "payments", ["payment_status", "paid_date"], unique=False)
    op.create_index(op.f("ix_payments_deleted_at"), "payments", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_payments_is_deleted"), "payments", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_payments_paid_date"), "payments", ["paid_date"], unique=False)
    op.create_index(op.f("ix_payments_payment_status"), "payments", ["payment_status"], unique=False)
    op.create_index(op.f("ix_payments_provider"), "payments", ["provider"], unique=False)
    op.create_index(op.f("ix_payments_transaction_ref"), "payments", ["transaction_ref"], unique=False)
    op.create_index(op.f("ix_payments_user_id"), "payments", ["user_id"], unique=False)

    op.create_table(
        "habit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("habit_name", sa.String(length=80), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("logged_hour", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_habit_logs_user_date", "habit_logs", ["user_id", "log_date"], unique=False)
    op.create_index("ix_habit_logs_user_habit_date", "habit_logs", ["user_id", "habit_name", "log_date"], unique=False)
    op.create_index(op.f("ix_habit_logs_deleted_at"), "habit_logs", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_habit_logs_habit_name"), "habit_logs", ["habit_name"], unique=False)
    op.create_index(op.f("ix_habit_logs_is_deleted"), "habit_logs", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_habit_logs_log_date"), "habit_logs", ["log_date"], unique=False)
    op.create_index(op.f("ix_habit_logs_logged_hour"), "habit_logs", ["logged_hour"], unique=False)
    op.create_index(op.f("ix_habit_logs_user_id"), "habit_logs", ["user_id"], unique=False)

    op.create_table(
        "conversions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("conversion_type", sa.String(length=40), nullable=False),
        sa.Column("value", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("conversion_date", sa.Date(), nullable=False),
        sa.Column("campaign_source", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversions_user_date", "conversions", ["user_id", "conversion_date"], unique=False)
    op.create_index("ix_conversions_type_date", "conversions", ["conversion_type", "conversion_date"], unique=False)
    op.create_index(op.f("ix_conversions_campaign_source"), "conversions", ["campaign_source"], unique=False)
    op.create_index(op.f("ix_conversions_conversion_date"), "conversions", ["conversion_date"], unique=False)
    op.create_index(op.f("ix_conversions_conversion_type"), "conversions", ["conversion_type"], unique=False)
    op.create_index(op.f("ix_conversions_deleted_at"), "conversions", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_conversions_is_deleted"), "conversions", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_conversions_session_id"), "conversions", ["session_id"], unique=False)
    op.create_index(op.f("ix_conversions_user_id"), "conversions", ["user_id"], unique=False)

    op.create_table(
        "campaign_tracking",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("utm_source", sa.String(length=120), nullable=True),
        sa.Column("utm_medium", sa.String(length=120), nullable=True),
        sa.Column("utm_campaign", sa.String(length=120), nullable=True),
        sa.Column("utm_term", sa.String(length=120), nullable=True),
        sa.Column("utm_content", sa.String(length=120), nullable=True),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_campaign_tracking_source_medium_campaign_date",
        "campaign_tracking",
        ["utm_source", "utm_medium", "utm_campaign", "visit_date"],
        unique=False,
    )
    op.create_index(op.f("ix_campaign_tracking_deleted_at"), "campaign_tracking", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_campaign_tracking_is_deleted"), "campaign_tracking", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_campaign_tracking_session_id"), "campaign_tracking", ["session_id"], unique=False)
    op.create_index(op.f("ix_campaign_tracking_user_id"), "campaign_tracking", ["user_id"], unique=False)
    op.create_index(op.f("ix_campaign_tracking_utm_campaign"), "campaign_tracking", ["utm_campaign"], unique=False)
    op.create_index(op.f("ix_campaign_tracking_utm_medium"), "campaign_tracking", ["utm_medium"], unique=False)
    op.create_index(op.f("ix_campaign_tracking_utm_source"), "campaign_tracking", ["utm_source"], unique=False)
    op.create_index(op.f("ix_campaign_tracking_visit_date"), "campaign_tracking", ["visit_date"], unique=False)

    op.create_table(
        "error_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("error_type", sa.String(length=120), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("stack_trace", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_error_logs_status_created", "error_logs", ["status_code", "created_at"], unique=False)
    op.create_index("ix_error_logs_path_created", "error_logs", ["path", "created_at"], unique=False)
    op.create_index(op.f("ix_error_logs_status_code"), "error_logs", ["status_code"], unique=False)
    op.create_index(op.f("ix_error_logs_trace_id"), "error_logs", ["trace_id"], unique=False)

    op.create_table(
        "daily_analytics_read_model",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("sessions_count", sa.Integer(), nullable=False),
        sa.Column("users_count", sa.Integer(), nullable=False),
        sa.Column("messages_count", sa.Integer(), nullable=False),
        sa.Column("revenue_total", sa.Float(), nullable=False),
        sa.Column("conversion_rate", sa.Float(), nullable=False),
        sa.Column("avg_productivity", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("metric_date"),
    )
    op.create_index("ix_daily_analytics_metric_date", "daily_analytics_read_model", ["metric_date"], unique=False)
    op.create_index(op.f("ix_daily_analytics_read_model_metric_date"), "daily_analytics_read_model", ["metric_date"], unique=False)

    op.create_table(
        "domain_event_outbox",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_name", sa.String(length=120), nullable=False),
        sa.Column("aggregate_id", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_domain_event_outbox_published_created", "domain_event_outbox", ["published", "created_at"], unique=False)
    op.create_index(op.f("ix_domain_event_outbox_aggregate_id"), "domain_event_outbox", ["aggregate_id"], unique=False)
    op.create_index(op.f("ix_domain_event_outbox_event_name"), "domain_event_outbox", ["event_name"], unique=False)
    op.create_index(op.f("ix_domain_event_outbox_published"), "domain_event_outbox", ["published"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_domain_event_outbox_published"), table_name="domain_event_outbox")
    op.drop_index(op.f("ix_domain_event_outbox_event_name"), table_name="domain_event_outbox")
    op.drop_index(op.f("ix_domain_event_outbox_aggregate_id"), table_name="domain_event_outbox")
    op.drop_index("ix_domain_event_outbox_published_created", table_name="domain_event_outbox")
    op.drop_table("domain_event_outbox")

    op.drop_index(op.f("ix_daily_analytics_read_model_metric_date"), table_name="daily_analytics_read_model")
    op.drop_index("ix_daily_analytics_metric_date", table_name="daily_analytics_read_model")
    op.drop_table("daily_analytics_read_model")

    op.drop_index(op.f("ix_error_logs_trace_id"), table_name="error_logs")
    op.drop_index(op.f("ix_error_logs_status_code"), table_name="error_logs")
    op.drop_index("ix_error_logs_path_created", table_name="error_logs")
    op.drop_index("ix_error_logs_status_created", table_name="error_logs")
    op.drop_table("error_logs")

    op.drop_index(op.f("ix_campaign_tracking_visit_date"), table_name="campaign_tracking")
    op.drop_index(op.f("ix_campaign_tracking_utm_source"), table_name="campaign_tracking")
    op.drop_index(op.f("ix_campaign_tracking_utm_medium"), table_name="campaign_tracking")
    op.drop_index(op.f("ix_campaign_tracking_utm_campaign"), table_name="campaign_tracking")
    op.drop_index(op.f("ix_campaign_tracking_user_id"), table_name="campaign_tracking")
    op.drop_index(op.f("ix_campaign_tracking_session_id"), table_name="campaign_tracking")
    op.drop_index(op.f("ix_campaign_tracking_is_deleted"), table_name="campaign_tracking")
    op.drop_index(op.f("ix_campaign_tracking_deleted_at"), table_name="campaign_tracking")
    op.drop_index("ix_campaign_tracking_source_medium_campaign_date", table_name="campaign_tracking")
    op.drop_table("campaign_tracking")

    op.drop_index(op.f("ix_conversions_user_id"), table_name="conversions")
    op.drop_index(op.f("ix_conversions_session_id"), table_name="conversions")
    op.drop_index(op.f("ix_conversions_is_deleted"), table_name="conversions")
    op.drop_index(op.f("ix_conversions_deleted_at"), table_name="conversions")
    op.drop_index(op.f("ix_conversions_conversion_type"), table_name="conversions")
    op.drop_index(op.f("ix_conversions_conversion_date"), table_name="conversions")
    op.drop_index(op.f("ix_conversions_campaign_source"), table_name="conversions")
    op.drop_index("ix_conversions_type_date", table_name="conversions")
    op.drop_index("ix_conversions_user_date", table_name="conversions")
    op.drop_table("conversions")

    op.drop_index(op.f("ix_habit_logs_user_id"), table_name="habit_logs")
    op.drop_index(op.f("ix_habit_logs_logged_hour"), table_name="habit_logs")
    op.drop_index(op.f("ix_habit_logs_log_date"), table_name="habit_logs")
    op.drop_index(op.f("ix_habit_logs_is_deleted"), table_name="habit_logs")
    op.drop_index(op.f("ix_habit_logs_habit_name"), table_name="habit_logs")
    op.drop_index(op.f("ix_habit_logs_deleted_at"), table_name="habit_logs")
    op.drop_index("ix_habit_logs_user_habit_date", table_name="habit_logs")
    op.drop_index("ix_habit_logs_user_date", table_name="habit_logs")
    op.drop_table("habit_logs")

    op.drop_index(op.f("ix_payments_user_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_transaction_ref"), table_name="payments")
    op.drop_index(op.f("ix_payments_provider"), table_name="payments")
    op.drop_index(op.f("ix_payments_payment_status"), table_name="payments")
    op.drop_index(op.f("ix_payments_paid_date"), table_name="payments")
    op.drop_index(op.f("ix_payments_is_deleted"), table_name="payments")
    op.drop_index(op.f("ix_payments_deleted_at"), table_name="payments")
    op.drop_index("ix_payments_status_date", table_name="payments")
    op.drop_index("ix_payments_user_paid_date", table_name="payments")
    op.drop_table("payments")

    op.drop_index(op.f("ix_messages_user_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_telegram_message_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_telegram_chat_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_message_type"), table_name="messages")
    op.drop_index(op.f("ix_messages_message_date"), table_name="messages")
    op.drop_index(op.f("ix_messages_is_deleted"), table_name="messages")
    op.drop_index(op.f("ix_messages_deleted_at"), table_name="messages")
    op.drop_index("ix_messages_chat_msgid", table_name="messages")
    op.drop_index("ix_messages_user_date_type", table_name="messages")
    op.drop_table("messages")

    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_refresh_token_jti"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_is_deleted"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_expires_at"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_deleted_at"), table_name="sessions")
    op.drop_index("ix_sessions_revoked", table_name="sessions")
    op.drop_index("ix_sessions_user_expires", table_name="sessions")
    op.drop_table("sessions")

    op.drop_index(op.f("ix_user_roles_user_id"), table_name="user_roles")
    op.drop_index(op.f("ix_user_roles_role_id"), table_name="user_roles")
    op.drop_table("user_roles")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_telegram_user_id"), table_name="users")
    op.drop_index(op.f("ix_users_is_deleted"), table_name="users")
    op.drop_index(op.f("ix_users_gender"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_deleted_at"), table_name="users")
    op.drop_index("ix_users_active_deleted", table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_roles_is_deleted"), table_name="roles")
    op.drop_index(op.f("ix_roles_deleted_at"), table_name="roles")
    op.drop_index("ix_roles_name_not_deleted", table_name="roles")
    op.drop_table("roles")
