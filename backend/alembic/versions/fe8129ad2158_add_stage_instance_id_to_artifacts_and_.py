"""add stage_instance_id to artifacts and review_comments

Revision ID: xxxxxxxxxxxx
Revises: 7c16b30c4e23
Create Date: 2026-01-26
"""
from alembic import op
import sqlalchemy as sa

revision = "fe8129ad2158"
down_revision = "ef4d32edf79e"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("artifacts", sa.Column("stage_instance_id", sa.Integer(), nullable=True))
    op.add_column("review_comments", sa.Column("stage_instance_id", sa.Integer(), nullable=True))

    # 先不加外键，避免你表名/约束没对齐导致再次爆炸
    # 等你确认 topic_stage_instances 表结构后再补 FK


def downgrade() -> None:
    op.drop_column("review_comments", "stage_instance_id")
    op.drop_column("artifacts", "stage_instance_id")
