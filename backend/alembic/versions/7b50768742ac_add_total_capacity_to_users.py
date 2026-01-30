"""add total_capacity to users

Revision ID: 7b50768742ac
Revises: 6d310bd045fe
Create Date: 2026-01-25 15:23:40.334383

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision = "7b50768742ac"
down_revision = "c323609dd40d"  # 这里确认一下是不是你的 head
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    exists = bind.execute(sa.text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='users' AND column_name='total_capacity'
    """)).scalar()

    if not exists:
        op.add_column(
            "users",
            sa.Column(
                "total_capacity",
                sa.Integer(),
                nullable=False,
                server_default="100",
            ),
        )
        # 保险：把已有行也补上（虽然 server_default 一般够）
        op.execute("UPDATE users SET total_capacity = 100 WHERE total_capacity IS NULL;")
        op.alter_column("users", "total_capacity", server_default=None)

def downgrade():
    bind = op.get_bind()
    exists = bind.execute(sa.text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='users' AND column_name='total_capacity'
    """)).scalar()
    if exists:
        op.drop_column("users", "total_capacity")
