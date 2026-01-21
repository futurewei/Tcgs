"""add stage deliverables table

Revision ID: add_stage_deliverables
Revises: xxxx_add_customer_and_requester
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_stage_deliverables'
down_revision = 'xxxx_add_customer_and_requester'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'stage_deliverables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('stage_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.Enum('file', 'link', name='deliverabletype'), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_name', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stage_id'], ['stage_template_stages.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stage_deliverables_id'), 'stage_deliverables', ['id'], unique=False)
    op.create_index(op.f('ix_stage_deliverables_topic_id'), 'stage_deliverables', ['topic_id'], unique=False)
    op.create_index(op.f('ix_stage_deliverables_stage_id'), 'stage_deliverables', ['stage_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_stage_deliverables_stage_id'), table_name='stage_deliverables')
    op.drop_index(op.f('ix_stage_deliverables_topic_id'), table_name='stage_deliverables')
    op.drop_index(op.f('ix_stage_deliverables_id'), table_name='stage_deliverables')
    op.drop_table('stage_deliverables')
    op.execute("DROP TYPE IF EXISTS deliverabletype")
