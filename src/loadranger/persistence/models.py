"""SQLAlchemy mappings for borrowers and immutable reporting periods."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all persistence mappings."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


class Borrower(Base):
    """A legal borrower entity with many financial reporting periods."""

    __tablename__ = "borrowers"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    legal_name: Mapped[str] = mapped_column(String(255), unique=True)
    financial_periods: Mapped[list["FinancialPeriod"]] = relationship(
        back_populates="borrower",
        order_by="FinancialPeriod.period_end",
    )


class FinancialPeriod(Base):
    """An immutable dated financial snapshot belonging to one borrower."""

    __tablename__ = "financial_periods"
    __table_args__ = (UniqueConstraint("borrower_id", "period_end"),)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    borrower_id: Mapped[UUID] = mapped_column(
        ForeignKey("borrowers.id"), nullable=False
    )
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), default="GBP")
    total_debt: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cash: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    ebitda: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    interest_expense: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    current_assets: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    current_liabilities: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    capital_expenditure: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    tax: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    borrower: Mapped[Borrower] = relationship(back_populates="financial_periods")
    metric_snapshots: Mapped[list["FinancialMetricSnapshot"]] = relationship(
        back_populates="financial_period",
        order_by="FinancialMetricSnapshot.created_at",
    )


class FinancialMetricSnapshot(Base):
    """An immutable application of one metric catalogue to a financial period."""

    __tablename__ = "financial_metric_snapshots"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    financial_period_id: Mapped[UUID] = mapped_column(
        ForeignKey("financial_periods.id"), nullable=False
    )
    calculation_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        server_default=func.now(),
    )
    financial_period: Mapped[FinancialPeriod] = relationship(
        back_populates="metric_snapshots"
    )
    metrics: Mapped[list["FinancialMetricSnapshotMetric"]] = relationship(
        back_populates="snapshot",
        order_by="FinancialMetricSnapshotMetric.name",
    )


class FinancialMetricSnapshotMetric(Base):
    """One metric result retained as evidence within a financial snapshot."""

    __tablename__ = "financial_metric_snapshot_metrics"
    __table_args__ = (UniqueConstraint("snapshot_id", "name"),)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("financial_metric_snapshots.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    value_scale: Mapped[int | None] = mapped_column(nullable=True)
    unavailable_reason: Mapped[str | None] = mapped_column(String(64))
    snapshot: Mapped[FinancialMetricSnapshot] = relationship(back_populates="metrics")
