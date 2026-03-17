"""add bots table

Revision ID: 20260302_0003
Revises: 20260302_0001
Create Date: 2026-03-02 18:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260302_0003"
down_revision: Union[str, Sequence[str], None] = "20260302_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("token", sa.String(length=2048), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bots_owner_created", "bots", ["owner_id", "created_at"], unique=False)
    op.create_index("ix_bots_owner_active", "bots", ["owner_id", "is_active"], unique=False)
    op.create_index("ix_bots_owner_deleted", "bots", ["owner_id", "is_deleted"], unique=False)
    op.create_index("ix_bots_owner_name", "bots", ["owner_id", "name"], unique=False)
    op.create_index(op.f("ix_bots_owner_id"), "bots", ["owner_id"], unique=False)
    op.create_index(op.f("ix_bots_is_active"), "bots", ["is_active"], unique=False)
    op.create_index(op.f("ix_bots_is_deleted"), "bots", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_bots_deleted_at"), "bots", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bots_deleted_at"), table_name="bots")
    op.drop_index(op.f("ix_bots_is_deleted"), table_name="bots")
    op.drop_index(op.f("ix_bots_is_active"), table_name="bots")
    op.drop_index(op.f("ix_bots_owner_id"), table_name="bots")
    op.drop_index("ix_bots_owner_deleted", table_name="bots")
    op.drop_index("ix_bots_owner_name", table_name="bots")
    op.drop_index("ix_bots_owner_active", table_name="bots")
    op.drop_index("ix_bots_owner_created", table_name="bots")
    op.drop_table("bots")
