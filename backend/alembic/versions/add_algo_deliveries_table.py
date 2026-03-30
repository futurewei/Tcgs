"""add algo_deliveries table

Revision ID: add_algo_deliveries_table
Revises: add_closed_at_to_topics
Create Date: 2026-03-30

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_algo_deliveries_table'
down_revision = 'add_closed_at_to_topics'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'algo_deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('month', sa.String(7), nullable=False, index=True),
        sa.Column('capability_name', sa.String(200), nullable=False),
        sa.Column('archive_url', sa.String(500), nullable=True),
        sa.Column('upgrade_description', sa.Text(), nullable=True),
        sa.Column('video_url', sa.String(500), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('delivered', sa.Boolean(), default=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_by_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.ForeignKeyConstraint(['delivered_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_algo_deliveries_id', 'algo_deliveries', ['id'])
    op.create_index('ix_algo_deliveries_month', 'algo_deliveries', ['month'])


def downgrade():
    op.drop_index('ix_algo_deliveries_month', table_name='algo_deliveries')
    op.drop_index('ix_algo_deliveries_id', table_name='algo_deliveries')
    op.drop_table('algo_deliveries')
