"""FastAPI dependencies for database-backed routes."""

import os
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session


@lru_cache
def _engine(database_url: str) -> Engine:
    return create_engine(database_url)


def get_session() -> Iterator[Session]:
    """Provide one database session per request."""
    database_url = os.getenv("LOADRANGER_DATABASE_URL")
    if database_url is None:
        raise RuntimeError("LOADRANGER_DATABASE_URL must be configured")
    with Session(_engine(database_url)) as session:
        yield session
