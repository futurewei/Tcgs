"""add_customer_and_requester

Revision ID: xxxx_add_customer_and_requester
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
# NOTE: If this is not the first migration, set down_revision to the latest migration's revision ID.
# To find the latest revision, check: alembic history | head -1
# Or check database: SELECT version_num FROM alembic_version;
revision = 'xxxx_add_customer_and_requester'
down_revision = None  # TODO: Replace with latest revision ID if migrations already exist
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Add CUSTOMER to user_role enum (must be autocommit for Postgres)
    ctx = op.get_context()
    with ctx.autocommit_block():
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'CUSTOMER'")

    # 2) Add requester fields to topics table
    op.add_column('topics', sa.Column('requester_name', sa.String(), nullable=False, server_default=''))
    op.add_column('topics', sa.Column('requester_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'topics_requester_user_id_fkey',
        'topics', 'users',
        ['requester_user_id'], ['id']
    )

    # Remove server default after adding the column (for existing rows)
    op.alter_column('topics', 'requester_name', server_default=None)


def downgrade() -> None:
    op.drop_constraint('topics_requester_user_id_fkey', 'topics', type_='foreignkey')
    op.drop_column('topics', 'requester_user_id')
    op.drop_column('topics', 'requester_name')
    # NOTE: enum value removal is intentionally skipped (Postgres limitation)
