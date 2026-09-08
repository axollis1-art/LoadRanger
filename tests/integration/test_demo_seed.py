"""Smoke coverage for the deterministic demonstration portfolio."""

import os
from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from alembic import command
from loadranger.api.dependencies import get_session
from loadranger.demo import (
    DEMO_BORROWER_NAMES,
    TRAJECTORY_BORROWER_NAME,
    seed_demo_data,
)
from loadranger.main import app
from loadranger.persistence.repository import BorrowerRepository

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
def session(engine: Engine) -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_seeded_demo_portfolio_is_idempotent_and_shows_trajectory(
    session: Session, client: TestClient
) -> None:
    first = seed_demo_data(session)
    second = seed_demo_data(session)

    assert set(first.borrower_ids) == set(DEMO_BORROWER_NAMES)
    assert second.borrower_ids == first.borrower_ids

    trajectory_id = first.borrower_ids[TRAJECTORY_BORROWER_NAME]
    summary = client.get(f"/borrowers/{trajectory_id}/credit-summary")

    assert summary.status_code == 200
    assert [test["status"] for test in summary.json()["covenant_tests"]] == [
        "breach",
        "warning",
        "pass",
    ]
    assert [alert["severity"] for alert in summary.json()["alerts"]] == [
        "breach",
        "warning",
    ]
    assert [
        (period.period_end, period.total_debt, period.cash, period.ebitda)
        for period in BorrowerRepository(session).list_financial_periods(trajectory_id)
    ] == [
        (date(2025, 12, 31), Decimal("400.00"), Decimal("100.00"), Decimal("100.00")),
        (date(2026, 12, 31), Decimal("450.00"), Decimal("100.00"), Decimal("100.00")),
        (date(2027, 12, 31), Decimal("520.00"), Decimal("100.00"), Decimal("100.00")),
    ]
