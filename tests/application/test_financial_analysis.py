"""Test-first specification for deterministic financial metric analysis."""

from decimal import Decimal

from loadranger.application.financial_analysis import (
    INITIAL_CALCULATION_VERSION,
    analyse_financial_inputs,
)
from loadranger.domain.financial import MetricUnavailableReason, Money
from loadranger.domain.metrics import FinancialInputs


def test_analysis_returns_versioned_values_and_unavailable_explanations() -> None:
    snapshot = analyse_financial_inputs(
        FinancialInputs(
            total_debt=Money(Decimal("100")),
            cash=Money(Decimal("25")),
            ebitda=None,
        )
    )

    assert snapshot.calculation_version == INITIAL_CALCULATION_VERSION
    assert snapshot.metrics["net_debt"].value == Decimal("75.00")
    assert snapshot.metrics["net_debt"].unavailable_reason is None
    assert snapshot.metrics["debt_to_ebitda"].value is None
    assert (
        snapshot.metrics["debt_to_ebitda"].unavailable_reason
        is MetricUnavailableReason.MISSING_INPUT
    )
