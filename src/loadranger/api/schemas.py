"""Validated public request and response contracts."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from loadranger.domain.financial import MetricUnavailableReason
from loadranger.domain.underwriting import (
    MetricComparison,
    RiskGrade,
    UnderwritingRecommendation,
)


class BorrowerCreate(BaseModel):
    legal_name: str = Field(max_length=255)

    @field_validator("legal_name")
    @classmethod
    def legal_name_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("legal_name must not be blank")
        return normalized


class BorrowerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    legal_name: str


class FinancialPeriodCreate(BaseModel):
    period_end: date
    currency_code: str = Field(default="GBP", pattern=r"^[A-Z]{3}$")
    total_debt: Decimal | None = None
    cash: Decimal | None = None
    ebitda: Decimal | None = None
    interest_expense: Decimal | None = None
    current_assets: Decimal | None = None
    current_liabilities: Decimal | None = None
    revenue: Decimal | None = None
    capital_expenditure: Decimal | None = None
    tax: Decimal | None = None


class FinancialPeriodResponse(FinancialPeriodCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    borrower_id: UUID


class MetricSnapshotMetricResponse(BaseModel):
    name: str
    value: Decimal | None
    unavailable_reason: MetricUnavailableReason | None


class FinancialMetricSnapshotResponse(BaseModel):
    id: UUID
    financial_period_id: UUID
    calculation_version: str
    created_at: datetime
    metrics: list[MetricSnapshotMetricResponse]


class UnderwritingFactorResponse(BaseModel):
    metric_name: str
    metric_value: Decimal
    comparison: MetricComparison
    threshold: Decimal
    score_adjustment: int
    description: str


class CreditAssessmentResponse(BaseModel):
    id: UUID
    borrower_id: UUID
    financial_period_id: UUID
    metric_snapshot_id: UUID
    policy_version: str
    score: int
    risk_grade: RiskGrade
    recommendation: UnderwritingRecommendation
    positive_factors: list[UnderwritingFactorResponse]
    risk_factors: list[UnderwritingFactorResponse]
    supporting_metrics: list[MetricSnapshotMetricResponse]
    created_at: datetime
