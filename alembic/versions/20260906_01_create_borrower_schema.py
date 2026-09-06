"""create borrower and financial period schema

Revision ID: 20260906_01
Revises:
Create Date: 2026-09-06
"""

import sqlalchemy as sa

from alembic import op

revision = "20260906_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "borrowers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("legal_name"),
    )
    op.create_table(
        "financial_periods",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("borrower_id", sa.Uuid(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("total_debt", sa.Numeric(precision=18, scale=2)),
        sa.Column("cash", sa.Numeric(precision=18, scale=2)),
        sa.Column("ebitda", sa.Numeric(precision=18, scale=2)),
        sa.Column("interest_expense", sa.Numeric(precision=18, scale=2)),
        sa.Column("current_assets", sa.Numeric(precision=18, scale=2)),
        sa.Column("current_liabilities", sa.Numeric(precision=18, scale=2)),
        sa.Column("revenue", sa.Numeric(precision=18, scale=2)),
        sa.Column("capital_expenditure", sa.Numeric(precision=18, scale=2)),
        sa.Column("tax", sa.Numeric(precision=18, scale=2)),
        sa.ForeignKeyConstraint(["borrower_id"], ["borrowers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("borrower_id", "period_end"),
    )
    op.execute("""
        CREATE FUNCTION prevent_financial_period_changes() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'financial periods are immutable';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER financial_periods_immutable
        BEFORE DELETE ON financial_periods
        FOR EACH ROW EXECUTE FUNCTION prevent_financial_period_changes();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER financial_periods_immutable ON financial_periods")
    op.execute("DROP FUNCTION prevent_financial_period_changes")
    op.drop_table("financial_periods")
    op.drop_table("borrowers")
