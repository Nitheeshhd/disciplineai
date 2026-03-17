"""refactor conversions for streak tracking

Revision ID: 20260302_0006
Revises: 20260302_0005
Create Date: 2026-03-02 21:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260302_0006"
down_revision: Union[str, Sequence[str], None] = "20260302_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_conversions_type_date")
    op.execute("DROP INDEX IF EXISTS ix_conversions_campaign_source")
    op.execute("DROP INDEX IF EXISTS ix_conversions_conversion_type")
    op.execute("DROP INDEX IF EXISTS ix_conversions_session_id")

    with op.batch_alter_table("conversions", recreate="always") as batch_op:
        batch_op.drop_column("session_id")
        batch_op.drop_column("conversion_type")
        batch_op.drop_column("value")
        batch_op.drop_column("campaign_source")
        batch_op.add_column(sa.Column("streak_length", sa.Integer(), nullable=False, server_default="7"))

    op.create_index("ix_conversions_user_streak", "conversions", ["user_id", "streak_length"], unique=False)
    with op.batch_alter_table("conversions") as batch_op:
        batch_op.alter_column("streak_length", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_conversions_user_streak", table_name="conversions")

    with op.batch_alter_table("conversions", recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column(
                "session_id",
                sa.Integer(),
                sa.ForeignKey("sessions.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column("conversion_type", sa.String(length=40), nullable=False, server_default="habit")
        )
        batch_op.add_column(sa.Column("value", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("campaign_source", sa.String(length=120), nullable=True))
        batch_op.drop_column("streak_length")

    op.create_index("ix_conversions_type_date", "conversions", ["conversion_type", "conversion_date"], unique=False)
    op.create_index("ix_conversions_campaign_source", "conversions", ["campaign_source"], unique=False)
    op.create_index("ix_conversions_conversion_type", "conversions", ["conversion_type"], unique=False)
    op.create_index("ix_conversions_session_id", "conversions", ["session_id"], unique=False)

    with op.batch_alter_table("conversions") as batch_op:
        batch_op.alter_column("conversion_type", server_default=None)
        batch_op.alter_column("value", server_default=None)

