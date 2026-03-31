"""add require_review to stages

Revision ID: a1b2c3d4e5f6
Revises: add_algo_deliveries_table
Create Date: 2026-03-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'add_algo_deliveries_table'
branch_labels = None
depends_on = None


def upgrade():
    # Add require_review to stage_template_stages
    op.add_column('stage_template_stages',
        sa.Column('require_review', sa.Boolean(), nullable=True, server_default='false')
    )

    # Add require_review to topic_stage_instances
    op.add_column('topic_stage_instances',
        sa.Column('require_review', sa.Boolean(), nullable=True, server_default='false')
    )


def downgrade():
    op.drop_column('topic_stage_instances', 'require_review')
    op.drop_column('stage_template_stages', 'require_review')
