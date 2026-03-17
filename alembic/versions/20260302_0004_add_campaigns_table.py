"""add campaigns table

Revision ID: 20260302_0004
Revises: 20260302_0003
Create Date: 2026-03-02 18:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260302_0004"
down_revision: Union[str, Sequence[str], None] = "20260302_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("base_url", sa.String(length=2048), nullable=False),
        sa.Column("utm_source", sa.String(length=120), nullable=False),
        sa.Column("utm_medium", sa.String(length=120), nullable=False),
        sa.Column("utm_campaign", sa.String(length=120), nullable=False),
        sa.Column("full_url", sa.String(length=4096), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_campaigns_user_created", "campaigns", ["user_id", "created_at"], unique=False)
    op.create_index(
        "ix_campaigns_user_utm_triplet",
        "campaigns",
        ["user_id", "utm_source", "utm_medium", "utm_campaign"],
        unique=False,
    )
    op.create_index(op.f("ix_campaigns_user_id"), "campaigns", ["user_id"], unique=False)
    op.create_index(op.f("ix_campaigns_utm_source"), "campaigns", ["utm_source"], unique=False)
    op.create_index(op.f("ix_campaigns_utm_medium"), "campaigns", ["utm_medium"], unique=False)
    op.create_index(op.f("ix_campaigns_utm_campaign"), "campaigns", ["utm_campaign"], unique=False)
    op.create_index(op.f("ix_campaigns_clicks"), "campaigns", ["clicks"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_campaigns_clicks"), table_name="campaigns")
    op.drop_index(op.f("ix_campaigns_utm_campaign"), table_name="campaigns")
    op.drop_index(op.f("ix_campaigns_utm_medium"), table_name="campaigns")
    op.drop_index(op.f("ix_campaigns_utm_source"), table_name="campaigns")
    op.drop_index(op.f("ix_campaigns_user_id"), table_name="campaigns")
    op.drop_index("ix_campaigns_user_utm_triplet", table_name="campaigns")
    op.drop_index("ix_campaigns_user_created", table_name="campaigns")
    op.drop_table("campaigns")

