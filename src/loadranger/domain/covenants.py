"""Direction-aware generic covenant evaluation and headroom calculations.

Absolute metrics report headroom in the metric's native units. Ratio metrics
report proportional headroom relative to the covenant threshold.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum

from loadranger.domain.financial import MetricResult, MetricUnavailableReason
from loadranger.persistence.models import CovenantOperator

HEADROOM_QUANTUM = Decimal("0.0001")
ABSOLUTE_METRICS = frozenset({"net_debt", "free_cash_flow"})


class CovenantEvaluationStatus(StrEnum):
    """The comparison outcome for a generic covenant."""

    PASS = "pass"
    WARNING = "warning"
    BREACH = "breach"
    NON_COMPARABLE = "non_comparable"


class HeadroomUnit(StrEnum):
    """Whether headroom is native metric units or a threshold proportion."""

    ABSOLUTE = "absolute"
    PROPORTIONAL = "proportional"


@dataclass(frozen=True, slots=True)
class CovenantEvaluation:
    """An explainable status, headroom, and unavailable-metric reason."""

    status: CovenantEvaluationStatus
    headroom: Decimal | None
    headroom_unit: HeadroomUnit | None
    unavailable_reason: MetricUnavailableReason | None


def evaluate_covenant(
    metric_name: str,
    metric: MetricResult,
    operator: CovenantOperator,
    threshold: Decimal,
    warning_threshold: Decimal | None,
) -> CovenantEvaluation:
    """Evaluate a covenant using only its metric result and declarative limits."""
    if metric.value is None:
        return CovenantEvaluation(
            status=CovenantEvaluationStatus.NON_COMPARABLE,
            headroom=None,
            headroom_unit=None,
            unavailable_reason=metric.reason,
        )
    if metric_name not in ABSOLUTE_METRICS and threshold == 0:
        return CovenantEvaluation(
            status=CovenantEvaluationStatus.NON_COMPARABLE,
            headroom=None,
            headroom_unit=None,
            unavailable_reason=MetricUnavailableReason.ZERO_DENOMINATOR,
        )

    status = _status(metric.value, operator, threshold, warning_threshold)
    headroom, headroom_unit = _headroom(metric_name, metric.value, operator, threshold)
    return CovenantEvaluation(
        status=status,
        headroom=headroom,
        headroom_unit=headroom_unit,
        unavailable_reason=None,
    )


def _status(
    value: Decimal,
    operator: CovenantOperator,
    threshold: Decimal,
    warning_threshold: Decimal | None,
) -> CovenantEvaluationStatus:
    if operator is CovenantOperator.AT_MOST:
        if value > threshold:
            return CovenantEvaluationStatus.BREACH
        if warning_threshold is not None and value >= warning_threshold:
            return CovenantEvaluationStatus.WARNING
    else:
        if value < threshold:
            return CovenantEvaluationStatus.BREACH
        if warning_threshold is not None and value <= warning_threshold:
            return CovenantEvaluationStatus.WARNING
    return CovenantEvaluationStatus.PASS


def _headroom(
    metric_name: str,
    value: Decimal,
    operator: CovenantOperator,
    threshold: Decimal,
) -> tuple[Decimal, HeadroomUnit]:
    difference = (
        threshold - value if operator is CovenantOperator.AT_MOST else value - threshold
    )
    if metric_name in ABSOLUTE_METRICS:
        return difference, HeadroomUnit.ABSOLUTE
    return (
        (difference / threshold).quantize(HEADROOM_QUANTUM, rounding=ROUND_HALF_EVEN),
        HeadroomUnit.PROPORTIONAL,
    )
