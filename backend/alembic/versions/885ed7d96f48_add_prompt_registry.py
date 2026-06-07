"""add_prompt_registry

Revision ID: 885ed7d96f48
Revises: 99ecd56cb2ce
Create Date: 2026-06-05 19:32:34.047049

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '885ed7d96f48'
down_revision = '99ecd56cb2ce'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'prompt_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('owner_user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table(
        'prompt_version',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prompt_template_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_by_user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['prompt_template_id'], ['prompt_template.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prompt_template_id', 'version_number', name='uq_prompt_version_template_id_version')
    )
    op.create_table(
        'prompt_assignment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prompt_template_id', sa.Integer(), nullable=False),
        sa.Column('target_type', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['prompt_template_id'], ['prompt_template.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('target_type', 'target_id', name='uq_prompt_assignment_target_type_id')
    )


def downgrade() -> None:
    op.drop_table('prompt_assignment')
    op.drop_table('prompt_version')
    op.drop_table('prompt_template')
