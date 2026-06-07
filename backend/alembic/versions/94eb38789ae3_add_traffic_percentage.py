"""add traffic_percentage

Revision ID: 94eb38789ae3
Revises: ec1c89aa863f
Create Date: 2026-06-06 22:31:35.072595

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '94eb38789ae3'
down_revision = 'ec1c89aa863f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("prompt_version", sa.Column("traffic_percentage", sa.Float(), nullable=False, server_default="0.0"))


def downgrade() -> None:
    op.drop_column("prompt_version", "traffic_percentage")
