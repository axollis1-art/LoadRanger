import os
from collections.abc import Iterator
from datetime import date

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from alembic import command
from loadranger.api.dependencies import get_session
from loadranger.main import app

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    database_url = os.getenv("LOADRANGER_DATABASE_URL")
    if database_url is None:
        pytest.skip(
            "LOADRANGER_DATABASE_URL is required for PostgreSQL integration tests"
        )
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(connection)
    app.dependency_overrides[get_session] = lambda: session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        session.close()
        transaction.rollback()
        connection.close()


def test_borrower_and_financial_period_workflow(client: TestClient) -> None:
    borrower_response = client.post(
        "/borrowers", json={"legal_name": "Acme Manufacturing Ltd"}
    )
    borrower = borrower_response.json()
    period_response = client.post(
        f"/borrowers/{borrower['id']}/financial-periods",
        json={"period_end": "2025-12-31", "currency_code": "GBP", "revenue": "100.00"},
    )

    assert borrower_response.status_code == 201
    assert client.get(f"/borrowers/{borrower['id']}").json() == borrower
    assert period_response.status_code == 201
    assert client.get(f"/borrowers/{borrower['id']}/financial-periods").json() == [
        {
            "id": period_response.json()["id"],
            "borrower_id": borrower["id"],
            "period_end": "2025-12-31",
            "currency_code": "GBP",
            "total_debt": None,
            "cash": None,
            "ebitda": None,
            "interest_expense": None,
            "current_assets": None,
            "current_liabilities": None,
            "revenue": "100.00",
            "capital_expenditure": None,
            "tax": None,
        }
    ]


def test_period_analysis_persists_metric_values_and_explanations(
    client: TestClient,
) -> None:
    borrower_id = client.post(
        "/borrowers", json={"legal_name": "Acme Manufacturing Ltd"}
    ).json()["id"]
    period_id = client.post(
        f"/borrowers/{borrower_id}/financial-periods",
        json={
            "period_end": "2025-12-31",
            "total_debt": "100.00",
            "cash": "25.00",
        },
    ).json()["id"]

    response = client.post(
        f"/borrowers/{borrower_id}/financial-periods/{period_id}/metric-snapshots"
    )

    assert response.status_code == 201
    snapshot = response.json()
    assert snapshot["financial_period_id"] == period_id
    assert snapshot["calculation_version"] == "v1"
    assert snapshot["metrics"] == [
        {
            "name": "current_ratio",
            "value": None,
            "unavailable_reason": "missing_input",
        },
        {
            "name": "debt_to_ebitda",
            "value": None,
            "unavailable_reason": "missing_input",
        },
        {
            "name": "ebitda_margin",
            "value": None,
            "unavailable_reason": "missing_input",
        },
        {
            "name": "free_cash_flow",
            "value": None,
            "unavailable_reason": "missing_input",
        },
        {
            "name": "interest_coverage",
            "value": None,
            "unavailable_reason": "missing_input",
        },
        {
            "name": "net_debt",
            "value": "75.00",
            "unavailable_reason": None,
        },
        {
            "name": "net_debt_to_ebitda",
            "value": None,
            "unavailable_reason": "missing_input",
        },
    ]


def test_reanalysing_a_period_retains_each_prior_metric_snapshot(
    client: TestClient,
) -> None:
    borrower_id = client.post(
        "/borrowers", json={"legal_name": "Acme Manufacturing Ltd"}
    ).json()["id"]
    period_id = client.post(
        f"/borrowers/{borrower_id}/financial-periods",
        json={"period_end": "2025-12-31", "total_debt": "100.00", "cash": "25.00"},
    ).json()["id"]
    path = f"/borrowers/{borrower_id}/financial-periods/{period_id}/metric-snapshots"

    first = client.post(path)
    second = client.post(path)
    history = client.get(path)

    assert first.status_code == 201
    assert second.status_code == 201
    assert history.status_code == 200
    assert [snapshot["id"] for snapshot in history.json()] == [
        first.json()["id"],
        second.json()["id"],
    ]


def test_missing_borrower_returns_404(client: TestClient) -> None:
    response = client.get("/borrowers/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "Borrower not found"}


@pytest.mark.parametrize(
    "payload",
    [
        {"legal_name": ""},
        {"legal_name": "   "},
    ],
)
def test_create_borrower_rejects_blank_legal_names(
    client: TestClient, payload: dict[str, str]
) -> None:
    assert client.post("/borrowers", json=payload).status_code == 422


def test_create_period_rejects_invalid_currency_code(client: TestClient) -> None:
    borrower_id = client.post(
        "/borrowers", json={"legal_name": "Acme Manufacturing Ltd"}
    ).json()["id"]

    response = client.post(
        f"/borrowers/{borrower_id}/financial-periods",
        json={"period_end": str(date(2025, 12, 31)), "currency_code": "UK"},
    )

    assert response.status_code == 422


def test_openapi_documents_borrower_and_financial_period_contracts() -> None:
    schema = app.openapi()

    assert "/borrowers" in schema["paths"]
    assert "/borrowers/{borrower_id}/financial-periods" in schema["paths"]
    assert "BorrowerCreate" in schema["components"]["schemas"]
    assert "FinancialPeriodCreate" in schema["components"]["schemas"]
