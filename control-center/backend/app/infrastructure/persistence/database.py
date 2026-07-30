"""SQLAlchemy database infrastructure."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)


class Base(DeclarativeBase):
    """Base class for infrastructure ORM models."""


def create_database_engine(
    database_url: str,
    *,
    echo: bool = False,
) -> Engine:
    """Create a SQLAlchemy engine for the configured database."""
    if not isinstance(database_url, str):
        raise TypeError("database_url must be a string")

    normalized_url = database_url.strip()

    if not normalized_url:
        raise ValueError("database_url must not be empty")

    connect_args: dict[str, object] = {}

    if normalized_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        normalized_url,
        echo=echo,
        connect_args=connect_args,
    )


def create_session_factory(
    engine: Engine,
) -> sessionmaker[Session]:
    """Create a configured synchronous SQLAlchemy session factory."""
    if not isinstance(engine, Engine):
        raise TypeError("engine must be a SQLAlchemy Engine")

    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )


@contextmanager
def session_scope(
    session_factory: sessionmaker[Session],
) -> Iterator[Session]:
    """Yield a session and manage commit, rollback, and closure."""
    session = session_factory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
