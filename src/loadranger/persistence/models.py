"""SQLAlchemy mappings for borrowers and immutable reporting periods."""

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all persistence mappings."""


class CovenantOperator(StrEnum):
    """The closed set of generic covenant breach directions."""

    AT_MOST = "<="
    AT_LEAST = ">="


class CovenantFrequency(StrEnum):
    """Supported assessment frequencies for generic covenants."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


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
    facilities: Mapped[list["Facility"]] = relationship(back_populates="borrower")


facility_covenants = Table(
    "facility_covenants",
    Base.metadata,
    Column(
        "facility_id", Uuid(as_uuid=True), ForeignKey("facilities.id"), primary_key=True
    ),
    Column(
        "covenant_definition_id",
        Uuid(as_uuid=True),
        ForeignKey("covenant_definitions.id"),
        primary_key=True,
    ),
)


class Facility(Base):
    """A borrower-owned lending facility with reusable covenant definitions."""

    __tablename__ = "facilities"
    __table_args__ = (UniqueConstraint("borrower_id", "name"),)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    borrower_id: Mapped[UUID] = mapped_column(
        ForeignKey("borrowers.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    borrower: Mapped[Borrower] = relationship(back_populates="facilities")
    covenants: Mapped[list["CovenantDefinition"]] = relationship(
        secondary=facility_covenants,
        back_populates="facilities",
    )


class CovenantDefinition(Base):
    """A reusable, declarative financial covenant definition."""

    __tablename__ = "covenant_definitions"
    __table_args__ = (
        UniqueConstraint("name"),
        CheckConstraint("operator IN ('<=', '>=')", name="covenant_operator"),
        CheckConstraint(
            "frequency IN ('monthly', 'quarterly', 'annually')",
            name="covenant_frequency",
        ),
        CheckConstraint(
            "warning_threshold IS NULL OR "
            "(operator = '<=' AND warning_threshold < threshold) OR "
            "(operator = '>=' AND warning_threshold > threshold)",
            name="covenant_warning_threshold",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    operator: Mapped[str] = mapped_column(String(2), nullable=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    warning_threshold: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    frequency: Mapped[str] = mapped_column(String(16), nullable=False)
    facilities: Mapped[list[Facility]] = relationship(
        secondary=facility_covenants,
        back_populates="covenants",
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


class CreditAssessment(Base):
    """An immutable, explainable underwriting decision for one reporting period."""

    __tablename__ = "credit_assessments"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    borrower_id: Mapped[UUID] = mapped_column(
        ForeignKey("borrowers.id"), nullable=False
    )
    financial_period_id: Mapped[UUID] = mapped_column(
        ForeignKey("financial_periods.id"), nullable=False
    )
    metric_snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("financial_metric_snapshots.id"), nullable=False
    )
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[int] = mapped_column(nullable=False)
    risk_grade: Mapped[str] = mapped_column(String(16), nullable=False)
    recommendation: Mapped[str] = mapped_column(String(16), nullable=False)
    positive_factors: Mapped[list[dict[str, str | int]]] = mapped_column(
        JSONB, nullable=False
    )
    risk_factors: Mapped[list[dict[str, str | int]]] = mapped_column(
        JSONB, nullable=False
    )
    supporting_metrics: Mapped[dict[str, dict[str, str | None]]] = mapped_column(
        JSONB, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        server_default=func.now(),
    )
