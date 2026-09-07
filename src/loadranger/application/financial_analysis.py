"""Deterministic analysis of a reporting period's financial inputs."""

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from loadranger.domain.financial import MetricResult, MetricUnavailableReason
from loadranger.domain.metrics import (
    FinancialInputs,
    calculate_current_ratio,
    calculate_debt_to_ebitda,
    calculate_ebitda_margin,
    calculate_free_cash_flow,
    calculate_interest_coverage,
    calculate_net_debt,
    calculate_net_debt_to_ebitda,
)

INITIAL_CALCULATION_VERSION = "v1"

MetricCalculation = Callable[[FinancialInputs], MetricResult]
METRIC_CALCULATIONS: dict[str, MetricCalculation] = {
    "net_debt": calculate_net_debt,
    "debt_to_ebitda": calculate_debt_to_ebitda,
    "net_debt_to_ebitda": calculate_net_debt_to_ebitda,
    "interest_coverage": calculate_interest_coverage,
    "current_ratio": calculate_current_ratio,
    "ebitda_margin": calculate_ebitda_margin,
    "free_cash_flow": calculate_free_cash_flow,
}


@dataclass(frozen=True, slots=True)
class AnalysedMetric:
    """A calculated metric value or the explicit reason it was unavailable."""

    value: Decimal | None
    unavailable_reason: MetricUnavailableReason | None


@dataclass(frozen=True, slots=True)
class AnalysedFinancialSnapshot:
    """The deterministic result of applying one catalogue version to inputs."""

    calculation_version: str
    metrics: dict[str, AnalysedMetric]


def analyse_financial_inputs(inputs: FinancialInputs) -> AnalysedFinancialSnapshot:
    """Apply the initial metric catalogue without hiding unavailable results."""
    return AnalysedFinancialSnapshot(
        calculation_version=INITIAL_CALCULATION_VERSION,
        metrics={
            name: AnalysedMetric(
                value=result.value,
                unavailable_reason=result.reason,
            )
            for name, calculation in METRIC_CALCULATIONS.items()
            for result in (calculation(inputs),)
        },
    )
