"""Repository operations for borrowers and financial periods."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from loadranger.domain.financial import FinancialInput
from loadranger.domain.metrics import FinancialInputs
from loadranger.persistence.models import Borrower, FinancialPeriod


class BorrowerRepository:
    """Transaction-bound persistence operations for the borrower aggregate."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_borrower(self, legal_name: str) -> Borrower:
        borrower = Borrower(legal_name=legal_name)
        self._session.add(borrower)
        self._session.flush()
        return borrower

    def record_financial_period(
        self,
        borrower_id: UUID,
        period_end: date,
        financial_inputs: FinancialInputs | None = None,
        currency_code: str = "GBP",
    ) -> FinancialPeriod:
        inputs = financial_inputs or FinancialInputs()
        period = FinancialPeriod(
            borrower_id=borrower_id,
            period_end=period_end,
            currency_code=currency_code,
            total_debt=_amount(inputs.total_debt),
            cash=_amount(inputs.cash),
            ebitda=_amount(inputs.ebitda),
            interest_expense=_amount(inputs.interest_expense),
            current_assets=_amount(inputs.current_assets),
            current_liabilities=_amount(inputs.current_liabilities),
            revenue=_amount(inputs.revenue),
            capital_expenditure=_amount(inputs.capital_expenditure),
            tax=_amount(inputs.tax),
        )
        self._session.add(period)
        self._session.flush()
        return period

    def list_financial_periods(self, borrower_id: UUID) -> list[FinancialPeriod]:
        statement = (
            select(FinancialPeriod)
            .where(FinancialPeriod.borrower_id == borrower_id)
            .order_by(FinancialPeriod.period_end)
        )
        return list(self._session.scalars(statement))


def _amount(value: FinancialInput) -> Decimal | None:
    return None if value is None else value.amount
