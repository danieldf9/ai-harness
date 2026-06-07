"""add_self_learning_models

Revision ID: ec1c89aa863f
Revises: 8df0d815b3ed
Create Date: 2026-06-05 21:42:18.893096

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ec1c89aa863f'
down_revision = '8df0d815b3ed'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'agent_run_trace',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('prompt_template_id', sa.Integer(), nullable=True),
        sa.Column('prompt_version_id', sa.Integer(), nullable=True),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('retrieval_strategy', sa.String(), nullable=False),
        sa.Column('tool_plan_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tools_called_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('citations_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('token_usage_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('outcome_status', sa.String(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('recovery_actions_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('final_resolution', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['prompt_template_id'], ['prompt_template.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['prompt_version_id'], ['prompt_version.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'user_feedback_signal',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_trace_id', sa.Integer(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('signal_type', sa.String(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('correction_text', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['run_trace_id'], ['agent_run_trace.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'healing_policy',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('target_type', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('low_confidence_threshold', sa.Float(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('allow_model_fallback', sa.Boolean(), nullable=False),
        sa.Column('allow_retrieval_expansion', sa.Boolean(), nullable=False),
        sa.Column('allow_retrieval_narrowing', sa.Boolean(), nullable=False),
        sa.Column('allow_tool_replan', sa.Boolean(), nullable=False),
        sa.Column('allow_prompt_fallback', sa.Boolean(), nullable=False),
        sa.Column('allow_human_escalation', sa.Boolean(), nullable=False),
        sa.Column('blocked_actions_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('environment', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'learning_recommendation',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('target_type', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=False),
        sa.Column('recommendation_type', sa.String(), nullable=False),
        sa.Column('current_config_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('proposed_config_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('evidence_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('impact_estimate_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('reviewed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'auto_optimization_rule',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('scope_type', sa.String(), nullable=False),
        sa.Column('scope_id', sa.String(), nullable=True),
        sa.Column('rule_type', sa.String(), nullable=False),
        sa.Column('guardrails_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('auto_optimization_rule')
    op.drop_table('learning_recommendation')
    op.drop_table('healing_policy')
    op.drop_table('user_feedback_signal')
    op.drop_table('agent_run_trace')
