"""add immutable financial metric snapshots

Revision ID: 20260907_01
Revises: 20260906_01
Create Date: 2026-09-07
"""

import sqlalchemy as sa

from alembic import op

revision = "20260907_01"
down_revision = "20260906_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "financial_metric_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("financial_period_id", sa.Uuid(), nullable=False),
        sa.Column("calculation_version", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["financial_period_id"], ["financial_periods.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "financial_metric_snapshot_metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Numeric(precision=18, scale=4)),
        sa.Column("value_scale", sa.Integer()),
        sa.Column("unavailable_reason", sa.String(length=64)),
        sa.ForeignKeyConstraint(["snapshot_id"], ["financial_metric_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("snapshot_id", "name"),
        sa.CheckConstraint(
            "(value IS NULL) <> (unavailable_reason IS NULL)",
            name="metric_value_or_reason",
        ),
        sa.CheckConstraint(
            "(value IS NULL) = (value_scale IS NULL)",
            name="metric_value_scale",
        ),
    )
    op.execute("""
        CREATE FUNCTION prevent_metric_snapshot_changes() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'metric snapshots are immutable';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER financial_metric_snapshots_immutable
        BEFORE UPDATE OR DELETE ON financial_metric_snapshots
        FOR EACH ROW EXECUTE FUNCTION prevent_metric_snapshot_changes();
    """)
    op.execute("""
        CREATE TRIGGER financial_metric_snapshot_metrics_immutable
        BEFORE UPDATE OR DELETE ON financial_metric_snapshot_metrics
        FOR EACH ROW EXECUTE FUNCTION prevent_metric_snapshot_changes();
    """)


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER financial_metric_snapshot_metrics_immutable "
        "ON financial_metric_snapshot_metrics"
    )
    op.execute(
        "DROP TRIGGER financial_metric_snapshots_immutable ON financial_metric_snapshots"
    )
    op.execute("DROP FUNCTION prevent_metric_snapshot_changes")
    op.drop_table("financial_metric_snapshot_metrics")
    op.drop_table("financial_metric_snapshots")
