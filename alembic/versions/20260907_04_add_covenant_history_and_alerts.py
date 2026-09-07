"""add covenant test history and alerts

Revision ID: 20260907_04
Revises: 20260907_03
"""

import sqlalchemy as sa

from alembic import op

revision = "20260907_04"
down_revision = "20260907_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "covenant_tests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("covenant_definition_id", sa.Uuid(), nullable=False),
        sa.Column("financial_period_id", sa.Uuid(), nullable=False),
        sa.Column("metric_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("headroom", sa.Numeric(18, 4)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["covenant_definition_id"], ["covenant_definitions.id"]
        ),
        sa.ForeignKeyConstraint(["financial_period_id"], ["financial_periods.id"]),
        sa.ForeignKeyConstraint(
            ["metric_snapshot_id"], ["financial_metric_snapshots.id"]
        ),
    )
    op.create_table(
        "covenant_alerts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("covenant_definition_id", sa.Uuid(), nullable=False),
        sa.Column("financial_period_id", sa.Uuid(), nullable=False),
        sa.Column("covenant_test_id", sa.Uuid(), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("lifecycle_status", sa.String(16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["covenant_definition_id"], ["covenant_definitions.id"]
        ),
        sa.ForeignKeyConstraint(["financial_period_id"], ["financial_periods.id"]),
        sa.ForeignKeyConstraint(["covenant_test_id"], ["covenant_tests.id"]),
        sa.UniqueConstraint(
            "covenant_definition_id", "financial_period_id", "severity"
        ),
    )
    op.execute(
        "CREATE FUNCTION prevent_covenant_test_changes() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'covenant tests are immutable'; END; $$ LANGUAGE plpgsql;"
    )
    op.execute(
        "CREATE TRIGGER covenant_tests_immutable BEFORE UPDATE OR DELETE ON covenant_tests FOR EACH ROW EXECUTE FUNCTION prevent_covenant_test_changes();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER covenant_tests_immutable ON covenant_tests")
    op.execute("DROP FUNCTION prevent_covenant_test_changes")
    op.drop_table("covenant_alerts")
    op.drop_table("covenant_tests")
