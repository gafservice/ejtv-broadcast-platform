"""Tests for the AuditRepository domain protocol."""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from app.domain.identity.entities import AuthenticatedIdentity
from app.domain.identity.protocols import AuditRepository
from app.domain.identity.value_objects import (
    PermissionName,
    RoleName,
    UserId,
    Username,
)


class FakeAuditRepository:
    """Minimal structural implementation used to validate the protocol."""

    def __init__(self) -> None:
        self.records: list[
            tuple[
                str,
                AuthenticatedIdentity | None,
                Mapping[str, str] | None,
            ]
        ] = []

    def record(
        self,
        event_type: str,
        identity: AuthenticatedIdentity | None,
        details: Mapping[str, str] | None = None,
    ) -> None:
        self.records.append((event_type, identity, details))


class IncompleteAuditRepository:
    """Object that intentionally does not satisfy the protocol."""

    def save(self, event_type: str) -> None:
        return None


def make_identity() -> AuthenticatedIdentity:
    """Build a representative authenticated identity."""

    return AuthenticatedIdentity(
        user_id=UserId(UUID("00000000-0000-0000-0000-000000000001")),
        username=Username("administrator"),
        roles=frozenset(
            {
                RoleName("administrator"),
            }
        ),
        permissions=frozenset(
            {
                PermissionName("dashboard.read"),
            }
        ),
    )


def test_complete_structural_implementation_satisfies_protocol() -> None:
    repository = FakeAuditRepository()

    assert isinstance(repository, AuditRepository)


def test_incomplete_implementation_does_not_satisfy_protocol() -> None:
    repository = IncompleteAuditRepository()

    assert not isinstance(repository, AuditRepository)


def test_protocol_exposes_record_operation() -> None:
    assert callable(getattr(AuditRepository, "record"))


def test_protocol_does_not_expose_storage_operations() -> None:
    assert not hasattr(AuditRepository, "commit")
    assert not hasattr(AuditRepository, "rollback")
    assert not hasattr(AuditRepository, "connect")
    assert not hasattr(AuditRepository, "execute")


def test_protocol_does_not_expose_observability_vendor_operations() -> None:
    assert not hasattr(AuditRepository, "send_to_loki")
    assert not hasattr(AuditRepository, "send_to_elasticsearch")
    assert not hasattr(AuditRepository, "send_to_syslog")


def test_repository_can_record_authenticated_event() -> None:
    repository = FakeAuditRepository()
    identity = make_identity()

    repository.record(
        event_type="authentication.succeeded",
        identity=identity,
        details={
            "source": "web",
        },
    )

    assert repository.records == [
        (
            "authentication.succeeded",
            identity,
            {
                "source": "web",
            },
        )
    ]


def test_repository_can_record_anonymous_event() -> None:
    repository = FakeAuditRepository()

    repository.record(
        event_type="authentication.failed",
        identity=None,
        details={
            "username": "unknown-user",
        },
    )

    assert repository.records == [
        (
            "authentication.failed",
            None,
            {
                "username": "unknown-user",
            },
        )
    ]


def test_repository_accepts_event_without_details() -> None:
    repository = FakeAuditRepository()
    identity = make_identity()

    repository.record(
        event_type="session.closed",
        identity=identity,
    )

    assert repository.records == [
        (
            "session.closed",
            identity,
            None,
        )
    ]
