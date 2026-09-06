"""Borrower and financial-period HTTP workflows."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from loadranger.api.dependencies import get_session
from loadranger.api.schemas import (
    BorrowerCreate,
    BorrowerResponse,
    FinancialPeriodCreate,
    FinancialPeriodResponse,
)
from loadranger.domain.financial import Money
from loadranger.domain.metrics import FinancialInputs
from loadranger.persistence.models import Borrower
from loadranger.persistence.repository import BorrowerRepository

router = APIRouter(prefix="/borrowers", tags=["borrowers"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post("", response_model=BorrowerResponse, status_code=status.HTTP_201_CREATED)
def create_borrower(
    payload: BorrowerCreate, session: SessionDependency
) -> BorrowerResponse:
    borrower = BorrowerRepository(session).create_borrower(payload.legal_name)
    session.commit()
    return BorrowerResponse.model_validate(borrower)


@router.get("/{borrower_id}", response_model=BorrowerResponse)
def get_borrower(borrower_id: UUID, session: SessionDependency) -> BorrowerResponse:
    borrower = _borrower_or_404(BorrowerRepository(session), borrower_id)
    return BorrowerResponse.model_validate(borrower)


@router.post(
    "/{borrower_id}/financial-periods",
    response_model=FinancialPeriodResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_financial_period(
    borrower_id: UUID,
    payload: FinancialPeriodCreate,
    session: SessionDependency,
) -> FinancialPeriodResponse:
    repository = BorrowerRepository(session)
    _borrower_or_404(repository, borrower_id)
    period = repository.record_financial_period(
        borrower_id,
        payload.period_end,
        _financial_inputs(payload),
        payload.currency_code,
    )
    session.commit()
    return FinancialPeriodResponse.model_validate(period)


@router.get(
    "/{borrower_id}/financial-periods", response_model=list[FinancialPeriodResponse]
)
def list_financial_periods(
    borrower_id: UUID,
    session: SessionDependency,
) -> list[FinancialPeriodResponse]:
    repository = BorrowerRepository(session)
    _borrower_or_404(repository, borrower_id)
    return [
        FinancialPeriodResponse.model_validate(period)
        for period in repository.list_financial_periods(borrower_id)
    ]


def _borrower_or_404(repository: BorrowerRepository, borrower_id: UUID) -> Borrower:
    borrower = repository.get_borrower(borrower_id)
    if borrower is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Borrower not found"
        )
    return borrower


def _financial_inputs(payload: FinancialPeriodCreate) -> FinancialInputs:
    return FinancialInputs(
        total_debt=_money(payload.total_debt),
        cash=_money(payload.cash),
        ebitda=_money(payload.ebitda),
        interest_expense=_money(payload.interest_expense),
        current_assets=_money(payload.current_assets),
        current_liabilities=_money(payload.current_liabilities),
        revenue=_money(payload.revenue),
        capital_expenditure=_money(payload.capital_expenditure),
        tax=_money(payload.tax),
    )


def _money(value: Decimal | None) -> Money | None:
    return None if value is None else Money(value)
