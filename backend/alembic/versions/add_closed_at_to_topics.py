"""add closed_at to topics

Revision ID: add_closed_at_to_topics
Revises: add_user_id_to_bindings
Create Date: 2026-03-29

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_closed_at_to_topics'
down_revision = 'fe8129ad2158'  # add_stage_instance_id_to_artifacts
branch_labels = None
depends_on = None


def upgrade():
    # 添加 closed_at 列
    op.add_column('topics', sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column('topics', 'closed_at')
