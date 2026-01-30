"""add background to topics

Revision ID: 1f3cd77be99b
Revises: 7b50768742ac
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1f3cd77be99b"
down_revision = "7b50768742ac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("topics", sa.Column("background", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("topics", "background")
