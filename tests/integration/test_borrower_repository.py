import os
from collections.abc import Iterator
from datetime import date

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine, inspect
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from loadranger.application.financial_analysis import analyse_financial_inputs
from loadranger.domain.metrics import FinancialInputs
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


def test_migration_creates_borrower_and_financial_period_tables(engine: Engine) -> None:
    tables = inspect(engine).get_table_names()

    assert "borrowers" in tables
    assert "financial_periods" in tables


def test_borrower_can_have_multiple_dated_reporting_periods(session: Session) -> None:
    repository = BorrowerRepository(session)
    borrower = repository.create_borrower("Acme Manufacturing Ltd")
    repository.record_financial_period(borrower.id, date(2025, 12, 31))
    repository.record_financial_period(borrower.id, date(2026, 12, 31))

    periods = repository.list_financial_periods(borrower.id)

    assert [period.period_end for period in periods] == [
        date(2025, 12, 31),
        date(2026, 12, 31),
    ]


def test_borrower_name_and_reporting_period_are_unique_per_borrower(
    session: Session,
) -> None:
    repository = BorrowerRepository(session)
    borrower = repository.create_borrower("Acme Manufacturing Ltd")
    repository.record_financial_period(borrower.id, date(2025, 12, 31))

    with pytest.raises(IntegrityError):
        repository.create_borrower("Acme Manufacturing Ltd")


def test_financial_period_cannot_be_changed_after_recording(session: Session) -> None:
    repository = BorrowerRepository(session)
    borrower = repository.create_borrower("Acme Manufacturing Ltd")
    period = repository.record_financial_period(borrower.id, date(2025, 12, 31))
    period.currency_code = "USD"

    with pytest.raises(DBAPIError, match="immutable"):
        session.flush()


def test_metric_snapshot_cannot_be_changed_after_recording(session: Session) -> None:
    repository = BorrowerRepository(session)
    borrower = repository.create_borrower("Acme Manufacturing Ltd")
    period = repository.record_financial_period(borrower.id, date(2025, 12, 31))
    snapshot = repository.create_metric_snapshot(
        period.id, analyse_financial_inputs(FinancialInputs())
    )
    snapshot.calculation_version = "v2"

    with pytest.raises(DBAPIError, match="immutable"):
        session.flush()
