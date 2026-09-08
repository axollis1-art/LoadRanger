"""Rendered dashboard smoke coverage."""

import os
from collections.abc import Iterator

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from alembic import command
from loadranger.api.dependencies import get_session
from loadranger.demo import TRAJECTORY_BORROWER_NAME, seed_demo_data
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


def test_dashboard_renders_seeded_credit_summary_with_htmx_fragment(
    session: Session, client: TestClient
) -> None:
    borrower_id = seed_demo_data(session).borrower_ids[TRAJECTORY_BORROWER_NAME]

    page = client.get(f"/dashboard/{borrower_id}")
    fragment = client.get(f"/dashboard/{borrower_id}/summary")

    assert page.status_code == 200
    assert TRAJECTORY_BORROWER_NAME in page.text
    assert f'hx-get="/dashboard/{borrower_id}/summary"' in page.text
    assert fragment.status_code == 200
    assert "Financial metrics" in fragment.text
    assert "4.2000" in fragment.text
    assert "Covenant history" in fragment.text
    assert "breach" in fragment.text
    assert "warning" in fragment.text
    assert "Open alerts" in fragment.text
