"""Add engine_type and hermes_config to Persona

Revision ID: f8cb67f38fb6
Revises: 94eb38789ae3
Create Date: 2026-06-09 13:24:08.787467

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8cb67f38fb6'
down_revision = '94eb38789ae3'
branch_labels = None
depends_on = None


from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    op.add_column('persona', sa.Column('engine_type', sa.String(), server_default='ONYX', nullable=False))
    op.add_column('persona', sa.Column('hermes_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

def downgrade() -> None:
    op.drop_column('persona', 'hermes_config')
    op.drop_column('persona', 'engine_type')
