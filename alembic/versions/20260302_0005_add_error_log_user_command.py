"""add user and command fields to error logs

Revision ID: 20260302_0005
Revises: 20260302_0004
Create Date: 2026-03-02 20:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260302_0005"
down_revision: Union[str, Sequence[str], None] = "20260302_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("error_logs", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column(
        "error_logs",
        sa.Column("command", sa.String(length=255), nullable=False, server_default="unknown"),
    )
    op.create_foreign_key(
        "fk_error_logs_user_id_users",
        "error_logs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_error_logs_user_id"), "error_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_error_logs_command"), "error_logs", ["command"], unique=False)
    op.create_index("ix_error_logs_user_created", "error_logs", ["user_id", "created_at"], unique=False)
    op.alter_column("error_logs", "command", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_error_logs_user_created", table_name="error_logs")
    op.drop_index(op.f("ix_error_logs_command"), table_name="error_logs")
    op.drop_index(op.f("ix_error_logs_user_id"), table_name="error_logs")
    op.drop_constraint("fk_error_logs_user_id_users", "error_logs", type_="foreignkey")
    op.drop_column("error_logs", "command")
    op.drop_column("error_logs", "user_id")

