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
    CovenantAlert,
    CovenantDefinition,
    CovenantFrequency,
    CovenantOperator,
    CovenantTest,
    CovenantTestStatus,
    CreditAssessment,
    Facility,
    FinancialMetricSnapshot,
    FinancialMetricSnapshotMetric,
    FinancialPeriod,
    facility_covenants,
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

    def create_facility(self, borrower_id: UUID, name: str) -> Facility:
        facility = Facility(borrower_id=borrower_id, name=name)
        self._session.add(facility)
        self._session.flush()
        return facility

    def create_covenant_definition(
        self,
        name: str,
        metric_name: str,
        operator: CovenantOperator,
        threshold: Decimal,
        warning_threshold: Decimal | None,
        frequency: CovenantFrequency,
    ) -> CovenantDefinition:
        covenant = CovenantDefinition(
            name=name,
            metric_name=metric_name,
            operator=operator.value,
            threshold=threshold,
            warning_threshold=warning_threshold,
            frequency=frequency.value,
        )
        self._session.add(covenant)
        self._session.flush()
        return covenant

    def attach_covenant_to_facility(
        self, facility_id: UUID, covenant_definition_id: UUID
    ) -> None:
        facility = self._session.get(Facility, facility_id)
        covenant = self._session.get(CovenantDefinition, covenant_definition_id)
        if facility is None or covenant is None:
            raise ValueError("facility and covenant definition must exist")
        facility.covenants.append(covenant)
        self._session.flush()

    def record_covenant_test(
        self,
        covenant_definition_id: UUID,
        financial_period_id: UUID,
        metric_snapshot_id: UUID,
        status: CovenantTestStatus,
        headroom: Decimal | None,
    ) -> CovenantTest:
        covenant_test = CovenantTest(
            covenant_definition_id=covenant_definition_id,
            financial_period_id=financial_period_id,
            metric_snapshot_id=metric_snapshot_id,
            status=status.value,
            headroom=headroom,
        )
        self._session.add(covenant_test)
        self._session.flush()
        if status in {CovenantTestStatus.WARNING, CovenantTestStatus.BREACH}:
            existing = self._session.scalar(
                select(CovenantAlert).where(
                    CovenantAlert.covenant_definition_id == covenant_definition_id,
                    CovenantAlert.financial_period_id == financial_period_id,
                    CovenantAlert.severity == status.value,
                )
            )
            if existing is None:
                self._session.add(
                    CovenantAlert(
                        covenant_definition_id=covenant_definition_id,
                        financial_period_id=financial_period_id,
                        covenant_test_id=covenant_test.id,
                        severity=status.value,
                        lifecycle_status="open",
                    )
                )
                self._session.flush()
        return covenant_test

    def list_alerts(
        self, covenant_definition_id: UUID, financial_period_id: UUID
    ) -> list[CovenantAlert]:
        return list(
            self._session.scalars(
                select(CovenantAlert)
                .where(
                    CovenantAlert.covenant_definition_id == covenant_definition_id,
                    CovenantAlert.financial_period_id == financial_period_id,
                )
                .order_by(CovenantAlert.created_at)
            )
        )

    def latest_metric_snapshot(
        self, borrower_id: UUID
    ) -> FinancialMetricSnapshot | None:
        return self._session.scalar(
            select(FinancialMetricSnapshot)
            .join(FinancialPeriod)
            .where(FinancialPeriod.borrower_id == borrower_id)
            .order_by(FinancialMetricSnapshot.created_at.desc())
        )

    def latest_credit_assessment(self, borrower_id: UUID) -> CreditAssessment | None:
        return self._session.scalar(
            select(CreditAssessment)
            .where(CreditAssessment.borrower_id == borrower_id)
            .order_by(CreditAssessment.created_at.desc())
        )

    def list_covenant_tests_for_borrower(self, borrower_id: UUID) -> list[CovenantTest]:
        return list(
            self._session.scalars(
                select(CovenantTest)
                .join(FinancialPeriod)
                .where(FinancialPeriod.borrower_id == borrower_id)
                .order_by(CovenantTest.created_at.desc())
            )
        )

    def list_alerts_for_borrower(self, borrower_id: UUID) -> list[CovenantAlert]:
        return list(
            self._session.scalars(
                select(CovenantAlert)
                .join(
                    CovenantDefinition,
                    CovenantDefinition.id == CovenantAlert.covenant_definition_id,
                )
                .join(
                    facility_covenants,
                    facility_covenants.c.covenant_definition_id
                    == CovenantDefinition.id,
                )
                .join(Facility, Facility.id == facility_covenants.c.facility_id)
                .where(Facility.borrower_id == borrower_id)
                .order_by(CovenantAlert.created_at.desc())
            )
        )

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
