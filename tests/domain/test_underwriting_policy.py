"""Test-first examples for the demonstrator underwriting policy."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from loadranger.domain.financial import MetricResult, MetricUnavailableReason
from loadranger.domain.underwriting import (
    DEMONSTRATOR_POLICY_V1,
    FactorKind,
    MetricComparison,
    MetricRule,
    RiskGrade,
    ScoreBand,
    UnderwritingPolicyConfiguration,
    UnderwritingRecommendation,
    evaluate_underwriting_policy,
)


def demonstrator_policy() -> UnderwritingPolicyConfiguration:
    return UnderwritingPolicyConfiguration(
        version="v1",
        starting_score=70,
        rules=[
            MetricRule(
                metric_name="net_debt_to_ebitda",
                comparison=MetricComparison.AT_MOST,
                threshold=Decimal("3.5000"),
                score_adjustment=15,
                factor_kind=FactorKind.POSITIVE,
                description="Leverage is within the demonstrator target.",
            ),
            MetricRule(
                metric_name="net_debt_to_ebitda",
                comparison=MetricComparison.AT_LEAST,
                threshold=Decimal("4.0000"),
                score_adjustment=-35,
                factor_kind=FactorKind.RISK,
                description="Leverage exceeds the demonstrator limit.",
            ),
            MetricRule(
                metric_name="interest_coverage",
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


def test_default_demonstrator_policy_is_a_versioned_data_configuration() -> None:
    assert DEMONSTRATOR_POLICY_V1.version == "v1"
    assert all(isinstance(rule, MetricRule) for rule in DEMONSTRATOR_POLICY_V1.rules)
    assert all(
        isinstance(score_band, ScoreBand)
        for score_band in DEMONSTRATOR_POLICY_V1.score_bands
    )


def test_policy_includes_score_grade_recommendation_factors_and_metrics() -> None:
    result = evaluate_underwriting_policy(
        demonstrator_policy(),
        {
            "net_debt_to_ebitda": MetricResult.available(Decimal("4.0000")),
            "interest_coverage": MetricResult.available(Decimal("3.0000")),
        },
    )

    assert result.policy_version == "v1"
    assert result.score == 40
    assert result.risk_grade is RiskGrade.HIGH
    assert result.recommendation is UnderwritingRecommendation.DECLINE
    assert [factor.description for factor in result.positive_factors] == [
        "Interest coverage supports repayment capacity."
    ]
    assert [factor.description for factor in result.risk_factors] == [
        "Leverage exceeds the demonstrator limit."
    ]
    assert result.supporting_metrics == {
        "net_debt_to_ebitda": MetricResult.available(Decimal("4.0000")),
        "interest_coverage": MetricResult.available(Decimal("3.0000")),
    }


def test_rule_boundaries_are_inclusive_and_unavailable_metrics_do_not_match() -> None:
    policy = demonstrator_policy()

    at_target = evaluate_underwriting_policy(
        policy,
        {
            "net_debt_to_ebitda": MetricResult.available(Decimal("3.5000")),
            "interest_coverage": MetricResult.unavailable(
                MetricUnavailableReason.MISSING_INPUT
            ),
        },
    )
    just_above_target = evaluate_underwriting_policy(
        policy,
        {
            "net_debt_to_ebitda": MetricResult.available(Decimal("3.5001")),
            "interest_coverage": MetricResult.unavailable(
                MetricUnavailableReason.MISSING_INPUT
            ),
        },
    )

    assert at_target.score == 85
    assert at_target.risk_grade is RiskGrade.LOW
    assert len(at_target.positive_factors) == 1
    assert just_above_target.score == 70
    assert just_above_target.positive_factors == []
    assert just_above_target.risk_factors == []
    assert (
        just_above_target.supporting_metrics["interest_coverage"].reason
        is MetricUnavailableReason.MISSING_INPUT
    )


def test_configuration_rejects_unknown_metrics_and_executable_expressions() -> None:
    with pytest.raises(ValidationError):
        UnderwritingPolicyConfiguration(
            version="v1",
            rules=[
                MetricRule(
                    metric_name="__import__('os').system('bad')",
                    comparison=MetricComparison.AT_LEAST,
                    threshold=Decimal("1"),
                    score_adjustment=1,
                    factor_kind=FactorKind.POSITIVE,
                    description="Unsafe expression",
                )
            ],
            score_bands=[
                ScoreBand(
                    minimum_score=0,
                    risk_grade=RiskGrade.HIGH,
                    recommendation=UnderwritingRecommendation.DECLINE,
                )
            ],
        )
