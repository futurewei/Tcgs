"""add is_dri to bindings

Revision ID: add_is_dri_to_bindings
Revises: xxxx_add_customer_and_requester
Create Date: 2026-01-22
"""
from alembic import op
import sqlalchemy as sa

revision = "add_is_dri_to_bindings"
down_revision = "xxxx_add_customer_and_requester"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bindings",
        sa.Column("is_dri", sa.Boolean(), nullable=True, server_default=sa.text("false")),
    )

    # 每个 topic 最早的一条 binding 标记为 DRI
    op.execute(sa.text("""
        WITH first_bindings AS (
            SELECT DISTINCT ON (topic_id) id
            FROM bindings
            ORDER BY topic_id, created_at ASC, id ASC
        )
        UPDATE bindings b
        SET is_dri = true
        FROM first_bindings fb
        WHERE b.id = fb.id
    """))

    op.execute(sa.text("UPDATE bindings SET is_dri = false WHERE is_dri IS NULL"))
    op.alter_column("bindings", "is_dri", nullable=False, server_default=sa.text("false"))


def downgrade() -> None:
    op.drop_column("bindings", "is_dri")
