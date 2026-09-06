"""Deterministic calculations for the initial commercial-credit metric catalogue."""

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from loadranger.domain.financial import (
    MONEY_QUANTUM,
    FinancialInput,
    MetricResult,
    MetricUnavailableReason,
)

RATIO_QUANTUM = Decimal("0.0001")


@dataclass(frozen=True, slots=True)
class FinancialInputs:
    """The financial inputs used by the initial metric catalogue.

    Each field is optional so missing source data remains distinguishable from a
    genuine monetary zero.
    """

    total_debt: FinancialInput = None
    cash: FinancialInput = None
    ebitda: FinancialInput = None
    interest_expense: FinancialInput = None
    current_assets: FinancialInput = None
    current_liabilities: FinancialInput = None
    revenue: FinancialInput = None
    capital_expenditure: FinancialInput = None
    tax: FinancialInput = None


def calculate_net_debt(inputs: FinancialInputs) -> MetricResult:
    """Calculate total debt less cash."""
    if inputs.total_debt is None or inputs.cash is None:
        return MetricResult.unavailable(MetricUnavailableReason.MISSING_INPUT)
    return _money_result(inputs.total_debt.amount - inputs.cash.amount)


def calculate_debt_to_ebitda(inputs: FinancialInputs) -> MetricResult:
    """Calculate total debt divided by EBITDA."""
    return _ratio(inputs.total_debt, inputs.ebitda)


def calculate_net_debt_to_ebitda(inputs: FinancialInputs) -> MetricResult:
    """Calculate net debt divided by EBITDA."""
    net_debt = calculate_net_debt(inputs)
    if net_debt.value is None:
        return net_debt
    return _ratio_value(net_debt.value, inputs.ebitda)


def calculate_interest_coverage(inputs: FinancialInputs) -> MetricResult:
    """Calculate EBITDA divided by cash interest expense."""
    return _ratio(inputs.ebitda, inputs.interest_expense)


def calculate_current_ratio(inputs: FinancialInputs) -> MetricResult:
    """Calculate current assets divided by current liabilities."""
    return _ratio(inputs.current_assets, inputs.current_liabilities)


def calculate_ebitda_margin(inputs: FinancialInputs) -> MetricResult:
    """Calculate EBITDA divided by revenue."""
    return _ratio(inputs.ebitda, inputs.revenue)


def calculate_free_cash_flow(inputs: FinancialInputs) -> MetricResult:
    """Calculate EBITDA less cash interest, tax, and capital expenditure."""
    required = (
        inputs.ebitda,
        inputs.interest_expense,
        inputs.tax,
        inputs.capital_expenditure,
    )
    if any(value is None for value in required):
        return MetricResult.unavailable(MetricUnavailableReason.MISSING_INPUT)
    ebitda, interest_expense, tax, capital_expenditure = required
    assert ebitda is not None
    assert interest_expense is not None
    assert tax is not None
    assert capital_expenditure is not None
    return _money_result(
        ebitda.amount
        - interest_expense.amount
        - tax.amount
        - capital_expenditure.amount
    )


def _ratio(numerator: FinancialInput, denominator: FinancialInput) -> MetricResult:
    if numerator is None:
        return MetricResult.unavailable(MetricUnavailableReason.MISSING_INPUT)
    return _ratio_value(numerator.amount, denominator)


def _ratio_value(numerator: Decimal, denominator: FinancialInput) -> MetricResult:
    if denominator is None:
        return MetricResult.unavailable(MetricUnavailableReason.MISSING_INPUT)
    if denominator.amount == 0:
        return MetricResult.unavailable(MetricUnavailableReason.ZERO_DENOMINATOR)
    if denominator.amount < 0:
        return MetricResult.unavailable(MetricUnavailableReason.NEGATIVE_DENOMINATOR)
    return MetricResult.available(
        (numerator / denominator.amount).quantize(
            RATIO_QUANTUM, rounding=ROUND_HALF_EVEN
        )
    )


def _money_result(value: Decimal) -> MetricResult:
    return MetricResult.available(
        value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)
    )
