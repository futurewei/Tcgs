"""merge heads

Revision ID: c323609dd40d
Revises: add_is_dri_to_bindings, add_stage_deliverables
Create Date: 2026-01-25 15:15:41.828642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c323609dd40d'
down_revision: Union[str, None] = ('add_is_dri_to_bindings', 'add_stage_deliverables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
