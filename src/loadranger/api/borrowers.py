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
    CreditAssessmentResponse,
    FinancialMetricSnapshotResponse,
    FinancialPeriodCreate,
    FinancialPeriodResponse,
    MetricSnapshotMetricResponse,
    UnderwritingFactorResponse,
)
from loadranger.application.financial_analysis import analyse_financial_inputs
from loadranger.domain.financial import MetricResult, MetricUnavailableReason, Money
from loadranger.domain.metrics import FinancialInputs
from loadranger.domain.underwriting import (
    DEMONSTRATOR_POLICY_V1,
    MetricComparison,
    RiskGrade,
    UnderwritingRecommendation,
    evaluate_underwriting_policy,
)
from loadranger.persistence.models import (
    Borrower,
    CreditAssessment,
    FinancialMetricSnapshot,
    FinancialPeriod,
)
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


@router.post(
    "/{borrower_id}/financial-periods/{financial_period_id}/metric-snapshots",
    response_model=FinancialMetricSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyse_financial_period(
    borrower_id: UUID,
    financial_period_id: UUID,
    session: SessionDependency,
) -> FinancialMetricSnapshotResponse:
    repository = BorrowerRepository(session)
    _borrower_or_404(repository, borrower_id)
    period = repository.get_financial_period(borrower_id, financial_period_id)
    if period is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Period not found"
        )
    snapshot = repository.create_metric_snapshot(
        financial_period_id,
        analyse_financial_inputs(_financial_inputs_from_period(period)),
    )
    session.commit()
    return _metric_snapshot_response(snapshot)


@router.get(
    "/{borrower_id}/financial-periods/{financial_period_id}/metric-snapshots",
    response_model=list[FinancialMetricSnapshotResponse],
)
def list_metric_snapshots(
    borrower_id: UUID,
    financial_period_id: UUID,
    session: SessionDependency,
) -> list[FinancialMetricSnapshotResponse]:
    repository = BorrowerRepository(session)
    _borrower_or_404(repository, borrower_id)
    if repository.get_financial_period(borrower_id, financial_period_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Period not found"
        )
    return [
        _metric_snapshot_response(snapshot)
        for snapshot in repository.list_metric_snapshots(financial_period_id)
    ]


@router.post(
    "/{borrower_id}/financial-periods/{financial_period_id}/credit-assessments",
    response_model=CreditAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_credit_assessment(
    borrower_id: UUID,
    financial_period_id: UUID,
    session: SessionDependency,
) -> CreditAssessmentResponse:
    repository = BorrowerRepository(session)
    _borrower_or_404(repository, borrower_id)
    period = repository.get_financial_period(borrower_id, financial_period_id)
    if period is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Period not found"
        )
    analysis = analyse_financial_inputs(_financial_inputs_from_period(period))
    metric_snapshot = repository.create_metric_snapshot(financial_period_id, analysis)
    decision = evaluate_underwriting_policy(
        DEMONSTRATOR_POLICY_V1,
        {
            name: MetricResult(
                value=metric.value,
                reason=metric.unavailable_reason,
            )
            for name, metric in analysis.metrics.items()
        },
    )
    assessment = repository.create_credit_assessment(
        borrower_id,
        financial_period_id,
        metric_snapshot.id,
        decision,
    )
    session.commit()
    return _credit_assessment_response(assessment)


@router.get(
    "/{borrower_id}/financial-periods/{financial_period_id}/credit-assessments/{assessment_id}",
    response_model=CreditAssessmentResponse,
)
def get_credit_assessment(
    borrower_id: UUID,
    financial_period_id: UUID,
    assessment_id: UUID,
    session: SessionDependency,
) -> CreditAssessmentResponse:
    repository = BorrowerRepository(session)
    _borrower_or_404(repository, borrower_id)
    if repository.get_financial_period(borrower_id, financial_period_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Period not found"
        )
    assessment = repository.get_credit_assessment(
        borrower_id, financial_period_id, assessment_id
    )
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )
    return _credit_assessment_response(assessment)


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


def _financial_inputs_from_period(period: FinancialPeriod) -> FinancialInputs:
    return FinancialInputs(
        total_debt=_money(period.total_debt),
        cash=_money(period.cash),
        ebitda=_money(period.ebitda),
        interest_expense=_money(period.interest_expense),
        current_assets=_money(period.current_assets),
        current_liabilities=_money(period.current_liabilities),
        revenue=_money(period.revenue),
        capital_expenditure=_money(period.capital_expenditure),
        tax=_money(period.tax),
    )


def _metric_snapshot_response(
    snapshot: FinancialMetricSnapshot,
) -> FinancialMetricSnapshotResponse:
    return FinancialMetricSnapshotResponse(
        id=snapshot.id,
        financial_period_id=snapshot.financial_period_id,
        calculation_version=snapshot.calculation_version,
        created_at=snapshot.created_at,
        metrics=[
            MetricSnapshotMetricResponse(
                name=metric.name,
                value=_value_with_recorded_scale(metric.value, metric.value_scale),
                unavailable_reason=(
                    None
                    if metric.unavailable_reason is None
                    else MetricUnavailableReason(metric.unavailable_reason)
                ),
            )
            for metric in snapshot.metrics
        ],
    )


def _credit_assessment_response(
    assessment: CreditAssessment,
) -> CreditAssessmentResponse:
    return CreditAssessmentResponse(
        id=assessment.id,
        borrower_id=assessment.borrower_id,
        financial_period_id=assessment.financial_period_id,
        metric_snapshot_id=assessment.metric_snapshot_id,
        policy_version=assessment.policy_version,
        score=assessment.score,
        risk_grade=RiskGrade(assessment.risk_grade),
        recommendation=UnderwritingRecommendation(assessment.recommendation),
        positive_factors=[
            _underwriting_factor_response(factor)
            for factor in assessment.positive_factors
        ],
        risk_factors=[
            _underwriting_factor_response(factor) for factor in assessment.risk_factors
        ],
        supporting_metrics=[
            MetricSnapshotMetricResponse(
                name=name,
                value=(None if metric["value"] is None else Decimal(metric["value"])),
                unavailable_reason=(
                    None
                    if metric["unavailable_reason"] is None
                    else MetricUnavailableReason(metric["unavailable_reason"])
                ),
            )
            for name, metric in sorted(assessment.supporting_metrics.items())
        ],
        created_at=assessment.created_at,
    )


def _underwriting_factor_response(
    factor: dict[str, str | int],
) -> UnderwritingFactorResponse:
    return UnderwritingFactorResponse(
        metric_name=str(factor["metric_name"]),
        metric_value=Decimal(str(factor["metric_value"])),
        comparison=MetricComparison(str(factor["comparison"])),
        threshold=Decimal(str(factor["threshold"])),
        score_adjustment=int(factor["score_adjustment"]),
        description=str(factor["description"]),
    )


def _value_with_recorded_scale(
    value: Decimal | None, scale: int | None
) -> Decimal | None:
    if value is None:
        return None
    assert scale is not None
    return value.quantize(Decimal(1).scaleb(-scale))


def _money(value: Decimal | None) -> Money | None:
    return None if value is None else Money(value)
