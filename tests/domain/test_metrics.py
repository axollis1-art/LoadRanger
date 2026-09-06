from collections.abc import Callable
from decimal import Decimal

import pytest

from loadranger.domain.financial import MetricResult, MetricUnavailableReason, Money
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


def money(amount: str) -> Money:
    return Money(Decimal(amount))


def complete_inputs(**overrides: Money | None) -> FinancialInputs:
    values: dict[str, Money | None] = {
        "total_debt": money("100"),
        "cash": money("25"),
        "ebitda": money("20"),
        "interest_expense": money("5"),
        "current_assets": money("40"),
        "current_liabilities": money("20"),
        "revenue": money("80"),
        "capital_expenditure": money("6"),
        "tax": money("2.5"),
    }
    values.update(overrides)
    return FinancialInputs(**values)


def assert_available(result: MetricResult, expected: str) -> None:
    assert result.value == Decimal(expected)
    assert result.reason is None


def test_net_debt_subtracts_cash_from_total_debt() -> None:
    assert_available(calculate_net_debt(complete_inputs()), "75.00")


def test_debt_to_ebitda_divides_total_debt_by_ebitda() -> None:
    assert_available(calculate_debt_to_ebitda(complete_inputs()), "5.0000")


def test_net_debt_to_ebitda_divides_net_debt_by_ebitda() -> None:
    assert_available(calculate_net_debt_to_ebitda(complete_inputs()), "3.7500")


def test_interest_coverage_divides_ebitda_by_cash_interest_expense() -> None:
    assert_available(calculate_interest_coverage(complete_inputs()), "4.0000")


def test_current_ratio_divides_current_assets_by_current_liabilities() -> None:
    assert_available(calculate_current_ratio(complete_inputs()), "2.0000")


def test_ebitda_margin_divides_ebitda_by_revenue() -> None:
    assert_available(calculate_ebitda_margin(complete_inputs()), "0.2500")


def test_free_cash_flow_subtracts_interest_tax_and_capex_from_ebitda() -> None:
    assert_available(calculate_free_cash_flow(complete_inputs()), "6.50")


@pytest.mark.parametrize(
    ("calculation", "zero_input", "negative_input"),
    [
        (calculate_debt_to_ebitda, {"ebitda": money("0")}, {"ebitda": money("-1")}),
        (
            calculate_net_debt_to_ebitda,
            {"ebitda": money("0")},
            {"ebitda": money("-1")},
        ),
        (
            calculate_interest_coverage,
            {"interest_expense": money("0")},
            {"interest_expense": money("-1")},
        ),
        (
            calculate_current_ratio,
            {"current_liabilities": money("0")},
            {"current_liabilities": money("-1")},
        ),
        (calculate_ebitda_margin, {"revenue": money("0")}, {"revenue": money("-1")}),
    ],
)
def test_ratios_report_zero_and_negative_denominators_as_unavailable(
    calculation: Callable[[FinancialInputs], MetricResult],
    zero_input: dict[str, Money],
    negative_input: dict[str, Money],
) -> None:
    assert (
        calculation(complete_inputs(**zero_input)).reason
        is MetricUnavailableReason.ZERO_DENOMINATOR
    )
    assert (
        calculation(complete_inputs(**negative_input)).reason
        is MetricUnavailableReason.NEGATIVE_DENOMINATOR
    )


@pytest.mark.parametrize(
    "calculation",
    [
        calculate_net_debt,
        calculate_debt_to_ebitda,
        calculate_net_debt_to_ebitda,
        calculate_interest_coverage,
        calculate_current_ratio,
        calculate_ebitda_margin,
        calculate_free_cash_flow,
    ],
)
def test_each_metric_reports_missing_inputs_as_unavailable(
    calculation: Callable[[FinancialInputs], MetricResult],
) -> None:
    result = calculation(FinancialInputs())

    assert result.value is None
    assert result.reason is MetricUnavailableReason.MISSING_INPUT
