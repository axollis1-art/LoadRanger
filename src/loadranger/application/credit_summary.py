"""Read use case for the borrower credit-summary views."""

from dataclasses import dataclass
from uuid import UUID

from loadranger.persistence.models import (
    Borrower,
    CovenantAlert,
    CovenantTest,
    CreditAssessment,
    FinancialMetricSnapshot,
)
from loadranger.persistence.repository import BorrowerRepository


@dataclass(frozen=True, slots=True)
class CreditSummary:
    borrower: Borrower
    snapshot: FinancialMetricSnapshot | None
    assessment: CreditAssessment | None
    covenant_tests: list[CovenantTest]
    alerts: list[CovenantAlert]


def get_credit_summary(
    repository: BorrowerRepository, borrower_id: UUID
) -> CreditSummary:
    """Load the immutable evidence shown by both API and dashboard views."""
    borrower = repository.get_borrower(borrower_id)
    if borrower is None:
        raise LookupError("Borrower not found")
    return CreditSummary(
        borrower=borrower,
        snapshot=repository.latest_metric_snapshot(borrower_id),
        assessment=repository.latest_credit_assessment(borrower_id),
        covenant_tests=repository.list_covenant_tests_for_borrower(borrower_id),
        alerts=repository.list_alerts_for_borrower(borrower_id),
    )
