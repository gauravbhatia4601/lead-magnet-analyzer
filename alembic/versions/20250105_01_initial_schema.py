"""Initial schema for sessions and analysis results.

Revision ID: 20250105_01
Revises: 
Create Date: 2025-01-05 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250105_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("requested_url", sa.String(length=2048), nullable=False),
        sa.Column("analysis_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("analysis_duration_seconds", sa.Float(), nullable=True),
        sa.Column("model_used", sa.String(length=128), nullable=True),
        sa.Column("metadata_snapshot", sa.JSON(), nullable=True),
        sa.Column("seo_scores", sa.JSON(), nullable=True),
        sa.Column("conversion_scores", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("insights", sa.JSON(), nullable=True),
        sa.Column("technical_issues", sa.JSON(), nullable=True),
        sa.Column("competitive_analysis", sa.JSON(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["app_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_results_requested_url", "analysis_results", ["requested_url"], unique=False)

    op.create_table(
        "analysis_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("requested_url", sa.String(length=2048), nullable=False),
        sa.Column("seo_overall_score", sa.Integer(), nullable=True),
        sa.Column("conversion_overall_score", sa.Integer(), nullable=True),
        sa.Column("headline", sa.String(length=256), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analysis_results.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["app_sessions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_history_session_id", "analysis_history", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_analysis_history_session_id", table_name="analysis_history")
    op.drop_table("analysis_history")
    op.drop_index("ix_analysis_results_requested_url", table_name="analysis_results")
    op.drop_table("analysis_results")
    op.drop_table("app_sessions")
