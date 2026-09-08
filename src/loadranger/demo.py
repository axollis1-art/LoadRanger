"""Deterministic demonstration portfolio data for a local LoadRanger database."""

import os
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from loadranger.application.financial_analysis import analyse_financial_inputs
from loadranger.domain.covenants import evaluate_covenant
from loadranger.domain.financial import MetricResult, Money
from loadranger.domain.metrics import FinancialInputs
from loadranger.domain.underwriting import (
    DEMONSTRATOR_POLICY_V1,
    evaluate_underwriting_policy,
)
from loadranger.persistence.models import (
    Borrower,
    CovenantFrequency,
    CovenantOperator,
    CovenantTestStatus,
)
from loadranger.persistence.repository import BorrowerRepository

DEMO_BORROWER_NAMES = (
    "Harbour Engineering Ltd",
    "Meridian Components Ltd",
    "Northstar Distribution Ltd",
)
TRAJECTORY_BORROWER_NAME = "Meridian Components Ltd"
DEMO_COVENANT_NAME = "Demo maximum net debt to EBITDA"
DEMO_COVENANT_THRESHOLD = Decimal("4.0000")
DEMO_COVENANT_WARNING_THRESHOLD = Decimal("3.5000")


@dataclass(frozen=True, slots=True)
class DemoSeedResult:
    """Identifiers of the stable named borrowers created by the seed."""

    borrower_ids: dict[str, UUID]


@dataclass(frozen=True, slots=True)
class _PeriodScenario:
    period_end: date
    total_debt: Decimal
    cash: Decimal
    ebitda: Decimal


_SCENARIOS: dict[str, tuple[_PeriodScenario, ...]] = {
    "Harbour Engineering Ltd": (
        _PeriodScenario(
            date(2027, 12, 31), Decimal("300"), Decimal("100"), Decimal("100")
        ),
    ),
    "Meridian Components Ltd": (
        _PeriodScenario(
            date(2025, 12, 31), Decimal("400"), Decimal("100"), Decimal("100")
        ),
        _PeriodScenario(
            date(2026, 12, 31), Decimal("450"), Decimal("100"), Decimal("100")
        ),
        _PeriodScenario(
            date(2027, 12, 31), Decimal("520"), Decimal("100"), Decimal("100")
        ),
    ),
    "Northstar Distribution Ltd": (
        _PeriodScenario(
            date(2027, 12, 31), Decimal("550"), Decimal("100"), Decimal("100")
        ),
    ),
}


def seed_demo_data(session: Session) -> DemoSeedResult:
    """Create the complete portfolio once, or return its stable identifiers.

    A partial portfolio is rejected rather than silently mixed with hand-managed
    data. This makes a repeated command safe while keeping its outcome explicit.
    """
    existing = {
        borrower.legal_name: borrower.id
        for borrower in session.scalars(
            select(Borrower).where(Borrower.legal_name.in_(DEMO_BORROWER_NAMES))
        )
    }
    if existing:
        if set(existing) != set(DEMO_BORROWER_NAMES):
            raise ValueError(
                "The demo portfolio is only partially present; remove the named "
                "demo borrowers before seeding again."
            )
        return DemoSeedResult(borrower_ids=existing)

    repository = BorrowerRepository(session)
    covenant = repository.create_covenant_definition(
        name=DEMO_COVENANT_NAME,
        metric_name="net_debt_to_ebitda",
        operator=CovenantOperator.AT_MOST,
        threshold=DEMO_COVENANT_THRESHOLD,
        warning_threshold=DEMO_COVENANT_WARNING_THRESHOLD,
        frequency=CovenantFrequency.ANNUALLY,
    )
    borrower_ids: dict[str, UUID] = {}
    for legal_name, periods in _SCENARIOS.items():
        borrower = repository.create_borrower(legal_name)
        borrower_ids[legal_name] = borrower.id
        facility = repository.create_facility(borrower.id, "Demonstration term loan")
        repository.attach_covenant_to_facility(facility.id, covenant.id)
        for period_scenario in periods:
            _seed_period(repository, borrower.id, covenant.id, period_scenario)

    return DemoSeedResult(borrower_ids=borrower_ids)


def _seed_period(
    repository: BorrowerRepository,
    borrower_id: UUID,
    covenant_id: UUID,
    scenario: _PeriodScenario,
) -> None:
    inputs = FinancialInputs(
        total_debt=Money(scenario.total_debt),
        cash=Money(scenario.cash),
        ebitda=Money(scenario.ebitda),
        interest_expense=Money(Decimal("20")),
        current_assets=Money(Decimal("200")),
        current_liabilities=Money(Decimal("100")),
        revenue=Money(Decimal("800")),
        capital_expenditure=Money(Decimal("30")),
        tax=Money(Decimal("20")),
    )
    period = repository.record_financial_period(
        borrower_id, scenario.period_end, inputs
    )
    analysis = analyse_financial_inputs(inputs)
    snapshot = repository.create_metric_snapshot(period.id, analysis)
    metrics = {
        name: MetricResult(value=metric.value, reason=metric.unavailable_reason)
        for name, metric in analysis.metrics.items()
    }
    repository.create_credit_assessment(
        borrower_id,
        period.id,
        snapshot.id,
        evaluate_underwriting_policy(DEMONSTRATOR_POLICY_V1, metrics),
    )
    evaluation = evaluate_covenant(
        "net_debt_to_ebitda",
        metrics["net_debt_to_ebitda"],
        CovenantOperator.AT_MOST,
        DEMO_COVENANT_THRESHOLD,
        DEMO_COVENANT_WARNING_THRESHOLD,
    )
    repository.record_covenant_test(
        covenant_id,
        period.id,
        snapshot.id,
        CovenantTestStatus(evaluation.status.value),
        evaluation.headroom,
    )


def main() -> int:
    """Seed the database selected by ``LOADRANGER_DATABASE_URL``."""
    database_url = os.getenv("LOADRANGER_DATABASE_URL")
    if database_url is None:
        raise SystemExit("LOADRANGER_DATABASE_URL must be configured")
    engine = create_engine(database_url)
    try:
        with Session(engine) as session:
            result = seed_demo_data(session)
            session.commit()
    finally:
        engine.dispose()
    print(f"Demo portfolio ready: {len(result.borrower_ids)} synthetic borrowers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
