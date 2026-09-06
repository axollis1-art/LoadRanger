from decimal import Decimal

import pytest

from loadranger.domain.financial import (
    MONEY_QUANTUM,
    MetricResult,
    MetricUnavailableReason,
    Money,
    is_missing,
)


def test_money_quantizes_normal_values_to_two_decimal_places() -> None:
    money = Money(Decimal("1234.567"))

    assert money.amount == Decimal("1234.57")
    assert money.amount.as_tuple().exponent == MONEY_QUANTUM.as_tuple().exponent


def test_money_preserves_genuine_zero_values() -> None:
    money = Money(Decimal("0"))

    assert money.amount == Decimal("0.00")
    assert is_missing(money) is False


def test_money_accepts_negative_values() -> None:
    money = Money(Decimal("-42.5"))

    assert money.amount == Decimal("-42.50")


def test_missing_financial_input_is_none_not_zero() -> None:
    assert is_missing(None) is True
    assert is_missing(Money(Decimal("0"))) is False


def test_metric_result_can_hold_an_available_value() -> None:
    result = MetricResult.available(Decimal("1.25"))

    assert result.value == Decimal("1.25")
    assert result.reason is None


def test_metric_result_can_hold_an_explicit_unavailable_reason() -> None:
    result = MetricResult.unavailable(MetricUnavailableReason.MISSING_INPUT)

    assert result.value is None
    assert result.reason is MetricUnavailableReason.MISSING_INPUT


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (Decimal("1"), MetricUnavailableReason.MISSING_INPUT),
        (None, None),
    ],
)
def test_metric_result_rejects_ambiguous_states(
    value: Decimal | None,
    reason: MetricUnavailableReason | None,
) -> None:
    with pytest.raises(ValueError, match="exactly one"):
        MetricResult(value=value, reason=reason)
