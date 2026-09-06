"""Validated public request and response contracts."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
