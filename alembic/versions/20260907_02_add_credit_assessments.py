"""add immutable credit assessments

Revision ID: 20260907_02
Revises: 20260907_01
Create Date: 2026-09-07
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260907_02"
down_revision = "20260907_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "credit_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("borrower_id", sa.Uuid(), nullable=False),
        sa.Column("financial_period_id", sa.Uuid(), nullable=False),
        sa.Column("metric_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("risk_grade", sa.String(length=16), nullable=False),
        sa.Column("recommendation", sa.String(length=16), nullable=False),
        sa.Column(
            "positive_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "risk_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "supporting_metrics",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["borrower_id"], ["borrowers.id"]),
        sa.ForeignKeyConstraint(["financial_period_id"], ["financial_periods.id"]),
        sa.ForeignKeyConstraint(
            ["metric_snapshot_id"], ["financial_metric_snapshots.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "score >= 0 AND score <= 100", name="assessment_score_range"
        ),
    )
    op.execute("""
        CREATE FUNCTION prevent_credit_assessment_changes() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'credit assessments are immutable';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER credit_assessments_immutable
        BEFORE UPDATE OR DELETE ON credit_assessments
        FOR EACH ROW EXECUTE FUNCTION prevent_credit_assessment_changes();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER credit_assessments_immutable ON credit_assessments")
    op.execute("DROP FUNCTION prevent_credit_assessment_changes")
    op.drop_table("credit_assessments")
