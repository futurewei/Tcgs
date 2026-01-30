from alembic import op
import sqlalchemy as sa

revision = "ef4d32edf79e"
down_revision = "7c16b30c4e23"
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column("topics", "dri_id", existing_type=sa.Integer(), nullable=True)

def downgrade():
    # 如果你回滚，要先把 NULL 补齐，否则会失败
    # 这里给一个保守策略：把 NULL 的 dri_id 设为 topics.requester_user_id 或某个管理员
    op.alter_column("topics", "dri_id", existing_type=sa.Integer(), nullable=False)
