"""add facilities and reusable covenant definitions

Revision ID: 20260907_03
Revises: 20260907_02
Create Date: 2026-09-07
"""

import sqlalchemy as sa

from alembic import op

revision = "20260907_03"
down_revision = "20260907_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "facilities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("borrower_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["borrower_id"], ["borrowers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("borrower_id", "name"),
    )
    op.create_table(
        "covenant_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("metric_name", sa.String(length=64), nullable=False),
        sa.Column("operator", sa.String(length=2), nullable=False),
        sa.Column("threshold", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("warning_threshold", sa.Numeric(precision=18, scale=4)),
        sa.Column("frequency", sa.String(length=16), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.CheckConstraint("operator IN ('<=', '>=')", name="covenant_operator"),
        sa.CheckConstraint(
            "frequency IN ('monthly', 'quarterly', 'annually')",
            name="covenant_frequency",
        ),
        sa.CheckConstraint(
            "warning_threshold IS NULL OR "
            "(operator = '<=' AND warning_threshold < threshold) OR "
            "(operator = '>=' AND warning_threshold > threshold)",
            name="covenant_warning_threshold",
        ),
    )
    op.create_table(
        "facility_covenants",
        sa.Column("facility_id", sa.Uuid(), nullable=False),
        sa.Column("covenant_definition_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"]),
        sa.ForeignKeyConstraint(
            ["covenant_definition_id"], ["covenant_definitions.id"]
        ),
        sa.PrimaryKeyConstraint("facility_id", "covenant_definition_id"),
    )


def downgrade() -> None:
    op.drop_table("facility_covenants")
    op.drop_table("covenant_definitions")
    op.drop_table("facilities")
