"""SQLAlchemy mappings for borrowers and immutable reporting periods."""

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all persistence mappings."""


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
