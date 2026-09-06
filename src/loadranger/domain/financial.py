"""Financial value types with explicit missing and unavailable semantics.

Money is stored in major currency units and quantized to two decimal places using
banker's rounding (``ROUND_HALF_EVEN``). Missing source data is represented by
``None``; it is never converted to a monetary zero.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum
from typing import Self

MONEY_QUANTUM = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class Money:
    """A finite, signed monetary amount quantized to two decimal places."""

    amount: Decimal

    def __post_init__(self) -> None:
        if not self.amount.is_finite():
            raise ValueError("money must be finite")
        object.__setattr__(
            self,
            "amount",
            self.amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN),
        )


type FinancialInput = Money | None


def is_missing(value: FinancialInput) -> bool:
    """Return whether a financial input was absent rather than zero."""
    return value is None


class MetricUnavailableReason(StrEnum):
    """Why a metric cannot safely produce a numeric value."""

    MISSING_INPUT = "missing_input"
    INVALID_INPUT = "invalid_input"
    ZERO_DENOMINATOR = "zero_denominator"
    NEGATIVE_DENOMINATOR = "negative_denominator"


@dataclass(frozen=True, slots=True)
class MetricResult:
    """A metric's numeric value or its explicit reason for being unavailable."""

    value: Decimal | None
    reason: MetricUnavailableReason | None

    def __post_init__(self) -> None:
        has_value = self.value is not None
        has_reason = self.reason is not None
        if has_value == has_reason:
            raise ValueError(
                "a metric result must contain exactly one of value or reason"
            )
        if self.value is not None and not self.value.is_finite():
            raise ValueError("a metric result value must be finite")

    @classmethod
    def available(cls, value: Decimal) -> Self:
        """Create a successfully calculated metric result."""
        return cls(value=value, reason=None)

    @classmethod
    def unavailable(cls, reason: MetricUnavailableReason) -> Self:
        """Create a result that preserves why calculation was unavailable."""
        return cls(value=None, reason=reason)
