"""Safe, deterministic configuration and evaluation for demonstrator underwriting."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from loadranger.domain.financial import MetricResult


class SupportedMetric(StrEnum):
    """Metrics that the initial demonstrator policy may reference."""

    NET_DEBT_TO_EBITDA = "net_debt_to_ebitda"
    INTEREST_COVERAGE = "interest_coverage"
    CURRENT_RATIO = "current_ratio"
    EBITDA_MARGIN = "ebitda_margin"
    FREE_CASH_FLOW = "free_cash_flow"


class MetricComparison(StrEnum):
    """Closed comparison set used by declarative policy rules."""

    AT_MOST = "at_most"
    AT_LEAST = "at_least"


class FactorKind(StrEnum):
    """Whether a matched rule supports or weakens the credit case."""

    POSITIVE = "positive"
    RISK = "risk"


class RiskGrade(StrEnum):
    """Coarse demonstrator risk grades derived from policy score bands."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UnderwritingRecommendation(StrEnum):
    """Demonstrator credit recommendations derived from policy score bands."""

    APPROVE = "approve"
    REFER = "refer"
    DECLINE = "decline"


class MetricRule(BaseModel):
    """One data-only scoring rule over a supported financial metric."""

    model_config = ConfigDict(frozen=True)

    metric_name: SupportedMetric
    comparison: MetricComparison
    threshold: Decimal
    score_adjustment: int
    factor_kind: FactorKind
    description: str = Field(min_length=1, max_length=255)

    @model_validator(mode="after")
    def score_adjustment_matches_factor_kind(self) -> "MetricRule":
        if self.factor_kind is FactorKind.POSITIVE and self.score_adjustment <= 0:
            raise ValueError("positive factors must increase the score")
        if self.factor_kind is FactorKind.RISK and self.score_adjustment >= 0:
            raise ValueError("risk factors must reduce the score")
        return self


class ScoreBand(BaseModel):
    """A score floor with its resulting grade and recommendation."""

    model_config = ConfigDict(frozen=True)

    minimum_score: int = Field(ge=0, le=100)
    risk_grade: RiskGrade
    recommendation: UnderwritingRecommendation


class UnderwritingPolicyConfiguration(BaseModel):
    """Validated, versioned declarative rules for one demonstrator policy."""

    model_config = ConfigDict(frozen=True)

    version: str = Field(pattern=r"^v[1-9][0-9]*$")
    starting_score: int = Field(ge=0, le=100)
    rules: list[MetricRule] = Field(min_length=1)
    score_bands: list[ScoreBand] = Field(min_length=1)

    @model_validator(mode="after")
    def score_bands_are_complete_and_descending(
        self,
    ) -> "UnderwritingPolicyConfiguration":
        minimum_scores = [band.minimum_score for band in self.score_bands]
        if minimum_scores != sorted(minimum_scores, reverse=True):
            raise ValueError("score bands must be ordered by descending minimum score")
        if len(set(minimum_scores)) != len(minimum_scores):
            raise ValueError("score band minimum scores must be unique")
        if minimum_scores[-1] != 0:
            raise ValueError("score bands must include a zero minimum score")
        return self


DEMONSTRATOR_POLICY_V1 = UnderwritingPolicyConfiguration(
    version="v1",
    starting_score=70,
    rules=[
        MetricRule(
            metric_name=SupportedMetric.NET_DEBT_TO_EBITDA,
            comparison=MetricComparison.AT_MOST,
            threshold=Decimal("3.5000"),
            score_adjustment=15,
            factor_kind=FactorKind.POSITIVE,
            description="Leverage is within the demonstrator target.",
        ),
        MetricRule(
            metric_name=SupportedMetric.NET_DEBT_TO_EBITDA,
            comparison=MetricComparison.AT_LEAST,
            threshold=Decimal("4.0000"),
            score_adjustment=-35,
            factor_kind=FactorKind.RISK,
            description="Leverage exceeds the demonstrator limit.",
        ),
        MetricRule(
            metric_name=SupportedMetric.INTEREST_COVERAGE,
            comparison=MetricComparison.AT_LEAST,
            threshold=Decimal("3.0000"),
            score_adjustment=5,
            factor_kind=FactorKind.POSITIVE,
            description="Interest coverage supports repayment capacity.",
        ),
    ],
    score_bands=[
        ScoreBand(
            minimum_score=80,
            risk_grade=RiskGrade.LOW,
            recommendation=UnderwritingRecommendation.APPROVE,
        ),
        ScoreBand(
            minimum_score=50,
            risk_grade=RiskGrade.MEDIUM,
            recommendation=UnderwritingRecommendation.REFER,
        ),
        ScoreBand(
            minimum_score=0,
            risk_grade=RiskGrade.HIGH,
            recommendation=UnderwritingRecommendation.DECLINE,
        ),
    ],
)


@dataclass(frozen=True, slots=True)
class UnderwritingFactor:
    """A matched, explainable rule and its contribution to the policy score."""

    metric_name: str
    metric_value: Decimal
    comparison: MetricComparison
    threshold: Decimal
    score_adjustment: int
    description: str


@dataclass(frozen=True, slots=True)
class UnderwritingDecision:
    """The transparent score, recommendation, factors, and source metrics."""

    policy_version: str
    score: int
    risk_grade: RiskGrade
    recommendation: UnderwritingRecommendation
    positive_factors: list[UnderwritingFactor]
    risk_factors: list[UnderwritingFactor]
    supporting_metrics: dict[str, MetricResult]


def evaluate_underwriting_policy(
    policy: UnderwritingPolicyConfiguration,
    metrics: Mapping[str, MetricResult],
) -> UnderwritingDecision:
    """Evaluate declarative rules without executing policy-supplied code."""
    score = policy.starting_score
    positive_factors: list[UnderwritingFactor] = []
    risk_factors: list[UnderwritingFactor] = []
    supporting_metrics: dict[str, MetricResult] = {}

    for rule in policy.rules:
        metric_name = rule.metric_name.value
        result = metrics.get(metric_name)
        if result is None:
            continue
        supporting_metrics[metric_name] = result
        if result.value is None or not _matches(rule, result.value):
            continue
        factor = UnderwritingFactor(
            metric_name=metric_name,
            metric_value=result.value,
            comparison=rule.comparison,
            threshold=rule.threshold,
            score_adjustment=rule.score_adjustment,
            description=rule.description,
        )
        score += rule.score_adjustment
        if rule.factor_kind is FactorKind.POSITIVE:
            positive_factors.append(factor)
        else:
            risk_factors.append(factor)

    bounded_score = min(100, max(0, score))
    score_band = next(
        band for band in policy.score_bands if bounded_score >= band.minimum_score
    )
    return UnderwritingDecision(
        policy_version=policy.version,
        score=bounded_score,
        risk_grade=score_band.risk_grade,
        recommendation=score_band.recommendation,
        positive_factors=positive_factors,
        risk_factors=risk_factors,
        supporting_metrics=supporting_metrics,
    )


def _matches(rule: MetricRule, value: Decimal) -> bool:
    if rule.comparison is MetricComparison.AT_MOST:
        return value <= rule.threshold
    return value >= rule.threshold
