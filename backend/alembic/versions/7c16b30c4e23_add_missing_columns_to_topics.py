"""add missing columns to topics

Revision ID: 7c16b30c4e23
Revises: de0616960894
Create Date: 2026-01-26
"""
from alembic import op
import sqlalchemy as sa

revision = "7c16b30c4e23"
down_revision = "de0616960894"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 后端 ORM/SQL 在查这两个字段，但 DB 里没有 -> 必须补
    op.add_column("topics", sa.Column("user_goal", sa.String(), nullable=True))
    op.add_column("topics", sa.Column("current_stage_instance_id", sa.Integer(), nullable=True))

    # 先不加外键，快速止血（等你确认表名/数据一致再补约束）
    # 如果你非常确定表名就是 topic_stage_instances，并且有 id 主键，再打开下面这段
    # op.create_foreign_key(
    #     "topics_current_stage_instance_id_fkey",
    #     "topics", "topic_stage_instances",
    #     ["current_stage_instance_id"], ["id"],
    # )


def downgrade() -> None:
    # 如果你加了外键，这里要先 drop_constraint
    # op.drop_constraint("topics_current_stage_instance_id_fkey", "topics", type_="foreignkey")
    op.drop_column("topics", "current_stage_instance_id")
    op.drop_column("topics", "user_goal")
