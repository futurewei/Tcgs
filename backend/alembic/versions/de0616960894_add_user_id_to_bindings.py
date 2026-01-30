"""add user_id to bindings

Revision ID: de0616960894
Revises: 1f3cd77be99b
Create Date: 2026-01-25
"""
from alembic import op
import sqlalchemy as sa

revision = "de0616960894"
down_revision = "1f3cd77be99b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bindings", sa.Column("user_id", sa.Integer(), nullable=True))

    # 回填：bindings.slot_id -> capacity_slots.user_id
    op.execute(sa.text("""
        UPDATE bindings b
        SET user_id = cs.user_id
        FROM capacity_slots cs
        WHERE b.slot_id = cs.id
          AND b.user_id IS NULL
    """))

    op.create_foreign_key(
        "bindings_user_id_fkey",
        "bindings", "users",
        ["user_id"], ["id"],
    )

    # 等你确认全部回填成功再考虑 NOT NULL
    # op.alter_column("bindings", "user_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint("bindings_user_id_fkey", "bindings", type_="foreignkey")
    op.drop_column("bindings", "user_id")
