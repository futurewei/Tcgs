"""add is_dri to bindings

Revision ID: add_is_dri_to_bindings
Revises: 
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_is_dri_to_bindings'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_dri column to bindings table
    op.add_column('bindings', sa.Column('is_dri', sa.Boolean(), nullable=True, server_default='false'))
    
    # Set the first binding of each topic as DRI
    connection = op.get_bind()
    
    # Get all topics
    result = connection.execute(sa.text("SELECT DISTINCT topic_id FROM bindings"))
    topic_ids = [row[0] for row in result]
    
    for topic_id in topic_ids:
        # Get the first binding for this topic (oldest created_at)
        first_binding = connection.execute(
            sa.text("SELECT id FROM bindings WHERE topic_id = :topic_id ORDER BY created_at ASC LIMIT 1"),
            {"topic_id": topic_id}
        ).fetchone()
        
        if first_binding:
            connection.execute(
                sa.text("UPDATE bindings SET is_dri = true WHERE id = :binding_id"),
                {"binding_id": first_binding[0]}
            )
    
    # Make is_dri not nullable with default false
    op.alter_column('bindings', 'is_dri', nullable=False, server_default='false')


def downgrade() -> None:
    op.drop_column('bindings', 'is_dri')
