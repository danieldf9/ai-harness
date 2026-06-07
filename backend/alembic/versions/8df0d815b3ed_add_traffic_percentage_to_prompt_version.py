"""add traffic_percentage to prompt_version

Revision ID: 8df0d815b3ed
Revises: 885ed7d96f48
Create Date: 2026-06-05 15:41:15.955003

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8df0d815b3ed'
down_revision = '885ed7d96f48'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('prompt_version', sa.Column('traffic_percentage', sa.Float(), nullable=False, server_default='0.0'))
    op.execute("UPDATE prompt_version SET traffic_percentage = 100.0 WHERE is_active = true")

def downgrade() -> None:
    op.drop_column('prompt_version', 'traffic_percentage')
