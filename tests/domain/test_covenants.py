"""Decision-table tests for generic covenant evaluation boundaries."""

from decimal import Decimal

import pytest

from loadranger.domain.covenants import (
    CovenantEvaluationStatus,
    HeadroomUnit,
    evaluate_covenant,
)
from loadranger.domain.financial import MetricResult, MetricUnavailableReason
from loadranger.persistence.models import CovenantOperator


@pytest.mark.parametrize(
    ("operator", "value", "expected_status"),
    [
        (CovenantOperator.AT_MOST, "3.5000", CovenantEvaluationStatus.WARNING),
        (CovenantOperator.AT_MOST, "4.0000", CovenantEvaluationStatus.WARNING),
        (CovenantOperator.AT_MOST, "4.0001", CovenantEvaluationStatus.BREACH),
        (CovenantOperator.AT_LEAST, "3.5000", CovenantEvaluationStatus.WARNING),
        (CovenantOperator.AT_LEAST, "3.0000", CovenantEvaluationStatus.WARNING),
        (CovenantOperator.AT_LEAST, "2.9999", CovenantEvaluationStatus.BREACH),
    ],
)
def test_covenant_boundaries_are_direction_aware(
    operator: CovenantOperator,
    value: str,
    expected_status: CovenantEvaluationStatus,
) -> None:
    result = evaluate_covenant(
        metric_name="net_debt_to_ebitda",
        metric=MetricResult.available(Decimal(value)),
        operator=operator,
        threshold=Decimal("4.0000")
        if operator is CovenantOperator.AT_MOST
        else Decimal("3.0000"),
        warning_threshold=Decimal("3.5000"),
    )

    assert result.status is expected_status


def test_covenant_returns_proportional_ratio_headroom_and_absolute_headroom() -> None:
    ratio = evaluate_covenant(
        metric_name="net_debt_to_ebitda",
        metric=MetricResult.available(Decimal("3.0000")),
        operator=CovenantOperator.AT_MOST,
        threshold=Decimal("4.0000"),
        warning_threshold=Decimal("3.5000"),
    )
    absolute = evaluate_covenant(
        metric_name="free_cash_flow",
        metric=MetricResult.available(Decimal("120.00")),
        operator=CovenantOperator.AT_LEAST,
        threshold=Decimal("100.00"),
        warning_threshold=Decimal("110.00"),
    )

    assert ratio.status is CovenantEvaluationStatus.PASS
    assert ratio.headroom == Decimal("0.2500")
    assert ratio.headroom_unit is HeadroomUnit.PROPORTIONAL
    assert absolute.status is CovenantEvaluationStatus.PASS
    assert absolute.headroom == Decimal("20.00")
    assert absolute.headroom_unit is HeadroomUnit.ABSOLUTE


def test_unavailable_metric_is_explicitly_non_comparable() -> None:
    result = evaluate_covenant(
        metric_name="current_ratio",
        metric=MetricResult.unavailable(MetricUnavailableReason.MISSING_INPUT),
        operator=CovenantOperator.AT_LEAST,
        threshold=Decimal("1.2500"),
        warning_threshold=Decimal("1.5000"),
    )

    assert result.status is CovenantEvaluationStatus.NON_COMPARABLE
    assert result.headroom is None
    assert result.unavailable_reason is MetricUnavailableReason.MISSING_INPUT
