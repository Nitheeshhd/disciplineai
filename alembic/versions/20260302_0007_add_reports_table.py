"""add reports table

Revision ID: 20260302_0007
Revises: 20260302_0006
Create Date: 2026-03-02 22:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260302_0007"
down_revision: Union[str, Sequence[str], None] = "20260302_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("total_users", sa.Integer(), nullable=False),
        sa.Column("avg_productivity", sa.Float(), nullable=False),
        sa.Column("revenue", sa.Float(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("week_start"),
    )
    op.create_index(op.f("ix_reports_week_start"), "reports", ["week_start"], unique=False)
    op.create_index("ix_reports_week_start_generated", "reports", ["week_start", "generated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_reports_week_start_generated", table_name="reports")
    op.drop_index(op.f("ix_reports_week_start"), table_name="reports")
    op.drop_table("reports")

