"""Integration tests for SQLAlchemyAuditRepository."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.identity.entities import AuthenticatedIdentity
from app.domain.identity.protocols import AuditRepository
from app.domain.identity.value_objects import (
    PermissionName,
    RoleName,
    UserId,
    Username,
)
from app.infrastructure.persistence.audit import (
    AuditLogModel,
    SQLAlchemyAuditRepository,
)
from app.infrastructure.persistence.database import Base


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


@pytest.fixture
def repository(
    session_factory: sessionmaker[Session],
) -> SQLAlchemyAuditRepository:
    return SQLAlchemyAuditRepository(session_factory)


def make_identity() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        user_id=UserId(
            UUID(
                "00000000-0000-0000-0000-000000000001"
            )
        ),
        username=Username("administrator"),
        roles=frozenset(
            {
                RoleName("operator"),
                RoleName("administrator"),
            }
        ),
        permissions=frozenset(
            {
                PermissionName("streams.manage"),
                PermissionName("dashboard.read"),
            }
        ),
    )


def get_records(
    session_factory: sessionmaker[Session],
) -> list[AuditLogModel]:
    with session_factory() as session:
        return list(
            session.scalars(
                select(AuditLogModel).order_by(
                    AuditLogModel.id
                )
            )
        )


def test_repository_satisfies_domain_protocol(
    repository: SQLAlchemyAuditRepository,
) -> None:
    assert isinstance(repository, AuditRepository)


def test_record_persists_authenticated_event(
    repository: SQLAlchemyAuditRepository,
    session_factory: sessionmaker[Session],
) -> None:
    repository.record(
        event_type="identity.login.succeeded",
        identity=make_identity(),
        details={
            "username": "administrator",
            "source": "web",
        },
    )

    records = get_records(session_factory)

    assert len(records) == 1

    record = records[0]

    assert record.id == 1
    assert record.event_type == "identity.login.succeeded"
    assert (
        record.user_id
        == "00000000-0000-0000-0000-000000000001"
    )
    assert record.username == "administrator"
    assert isinstance(record.occurred_at, datetime)

    assert json.loads(record.roles_json) == [
        "administrator",
        "operator",
    ]

    assert json.loads(record.permissions_json) == [
        "dashboard.read",
        "streams.manage",
    ]

    assert json.loads(record.details_json) == {
        "source": "web",
        "username": "administrator",
    }


def test_record_persists_anonymous_event(
    repository: SQLAlchemyAuditRepository,
    session_factory: sessionmaker[Session],
) -> None:
    repository.record(
        event_type="identity.login.failed",
        identity=None,
        details={
            "username": "unknown-user",
        },
    )

    record = get_records(session_factory)[0]

    assert record.event_type == "identity.login.failed"
    assert record.user_id is None
    assert record.username is None
    assert record.roles_json is None
    assert record.permissions_json is None

    assert json.loads(record.details_json) == {
        "username": "unknown-user",
    }


def test_record_accepts_event_without_details(
    repository: SQLAlchemyAuditRepository,
    session_factory: sessionmaker[Session],
) -> None:
    repository.record(
        event_type="session.closed",
        identity=make_identity(),
    )

    record = get_records(session_factory)[0]

    assert record.details_json is None


def test_record_preserves_multiple_events(
    repository: SQLAlchemyAuditRepository,
    session_factory: sessionmaker[Session],
) -> None:
    identity = make_identity()

    repository.record(
        "identity.authorization.succeeded",
        identity,
        {
            "permission": "dashboard.read",
        },
    )

    repository.record(
        "identity.authorization.denied",
        identity,
        {
            "permission": "users.manage",
        },
    )

    records = get_records(session_factory)

    assert [record.id for record in records] == [1, 2]

    assert [
        record.event_type
        for record in records
    ] == [
        "identity.authorization.succeeded",
        "identity.authorization.denied",
    ]


def test_record_strips_event_type_whitespace(
    repository: SQLAlchemyAuditRepository,
    session_factory: sessionmaker[Session],
) -> None:
    repository.record(
        "  identity.login.succeeded  ",
        make_identity(),
    )

    record = get_records(session_factory)[0]

    assert record.event_type == "identity.login.succeeded"


@pytest.mark.parametrize(
    "event_type",
    [
        "",
        " ",
        "\n\t",
    ],
)
def test_record_rejects_empty_event_type(
    repository: SQLAlchemyAuditRepository,
    event_type: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="event_type must not be empty",
    ):
        repository.record(
            event_type,
            None,
        )


def test_record_rejects_non_string_event_type(
    repository: SQLAlchemyAuditRepository,
) -> None:
    with pytest.raises(
        TypeError,
        match="event_type must be a string",
    ):
        repository.record(123, None)  # type: ignore[arg-type]


def test_record_rejects_invalid_identity(
    repository: SQLAlchemyAuditRepository,
) -> None:
    with pytest.raises(
        TypeError,
        match=(
            "identity must be an "
            "AuthenticatedIdentity or None"
        ),
    ):
        repository.record(
            "identity.login.succeeded",
            object(),  # type: ignore[arg-type]
        )


def test_record_rejects_non_string_detail_values(
    repository: SQLAlchemyAuditRepository,
) -> None:
    with pytest.raises(
        TypeError,
        match="detail values must be strings",
    ):
        repository.record(
            "identity.login.succeeded",
            make_identity(),
            {
                "attempt": 1,  # type: ignore[dict-item]
            },
        )
