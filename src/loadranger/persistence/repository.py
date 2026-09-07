"""Repository operations for borrowers and financial periods."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from loadranger.application.financial_analysis import AnalysedFinancialSnapshot
from loadranger.domain.financial import FinancialInput, MetricResult
from loadranger.domain.metrics import FinancialInputs
from loadranger.domain.underwriting import UnderwritingDecision, UnderwritingFactor
from loadranger.persistence.models import (
    Borrower,
    CreditAssessment,
    FinancialMetricSnapshot,
    FinancialMetricSnapshotMetric,
    FinancialPeriod,
)


class BorrowerRepository:
    """Transaction-bound persistence operations for the borrower aggregate."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_borrower(self, legal_name: str) -> Borrower:
        borrower = Borrower(legal_name=legal_name)
        self._session.add(borrower)
        self._session.flush()
        return borrower

    def get_borrower(self, borrower_id: UUID) -> Borrower | None:
        return self._session.get(Borrower, borrower_id)

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

    def get_financial_period(
        self, borrower_id: UUID, financial_period_id: UUID
    ) -> FinancialPeriod | None:
        statement = select(FinancialPeriod).where(
            FinancialPeriod.id == financial_period_id,
            FinancialPeriod.borrower_id == borrower_id,
        )
        return self._session.scalar(statement)

    def create_metric_snapshot(
        self,
        financial_period_id: UUID,
        analysis: AnalysedFinancialSnapshot,
    ) -> FinancialMetricSnapshot:
        snapshot = FinancialMetricSnapshot(
            financial_period_id=financial_period_id,
            calculation_version=analysis.calculation_version,
            metrics=[
                FinancialMetricSnapshotMetric(
                    name=name,
                    value=metric.value,
                    value_scale=(
                        None if metric.value is None else _decimal_scale(metric.value)
                    ),
                    unavailable_reason=(
                        None
                        if metric.unavailable_reason is None
                        else metric.unavailable_reason.value
                    ),
                )
                for name, metric in analysis.metrics.items()
            ],
        )
        self._session.add(snapshot)
        self._session.flush()
        return snapshot

    def list_metric_snapshots(
        self, financial_period_id: UUID
    ) -> list[FinancialMetricSnapshot]:
        statement = (
            select(FinancialMetricSnapshot)
            .where(FinancialMetricSnapshot.financial_period_id == financial_period_id)
            .order_by(FinancialMetricSnapshot.created_at, FinancialMetricSnapshot.id)
        )
        return list(self._session.scalars(statement))

    def create_credit_assessment(
        self,
        borrower_id: UUID,
        financial_period_id: UUID,
        metric_snapshot_id: UUID,
        decision: UnderwritingDecision,
    ) -> CreditAssessment:
        assessment = CreditAssessment(
            borrower_id=borrower_id,
            financial_period_id=financial_period_id,
            metric_snapshot_id=metric_snapshot_id,
            policy_version=decision.policy_version,
            score=decision.score,
            risk_grade=decision.risk_grade.value,
            recommendation=decision.recommendation.value,
            positive_factors=[
                _factor_document(factor) for factor in decision.positive_factors
            ],
            risk_factors=[_factor_document(factor) for factor in decision.risk_factors],
            supporting_metrics={
                name: _metric_document(result)
                for name, result in decision.supporting_metrics.items()
            },
        )
        self._session.add(assessment)
        self._session.flush()
        return assessment

    def get_credit_assessment(
        self,
        borrower_id: UUID,
        financial_period_id: UUID,
        assessment_id: UUID,
    ) -> CreditAssessment | None:
        statement = select(CreditAssessment).where(
            CreditAssessment.id == assessment_id,
            CreditAssessment.borrower_id == borrower_id,
            CreditAssessment.financial_period_id == financial_period_id,
        )
        return self._session.scalar(statement)


def _amount(value: FinancialInput) -> Decimal | None:
    return None if value is None else value.amount


def _decimal_scale(value: Decimal) -> int:
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int):
        raise ValueError("metric values must be finite")
    return max(0, -exponent)


def _factor_document(factor: UnderwritingFactor) -> dict[str, str | int]:
    return {
        "metric_name": factor.metric_name,
        "metric_value": str(factor.metric_value),
        "comparison": factor.comparison.value,
        "threshold": str(factor.threshold),
        "score_adjustment": factor.score_adjustment,
        "description": factor.description,
    }


def _metric_document(result: MetricResult) -> dict[str, str | None]:
    return {
        "value": None if result.value is None else str(result.value),
        "unavailable_reason": None if result.reason is None else result.reason.value,
    }
