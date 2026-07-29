from collections.abc import Mapping
from uuid import UUID

import pytest

from app.domain.identity.entities import AuthenticatedIdentity
from app.domain.identity.exceptions import PermissionDenied
from app.domain.identity.value_objects import (
    PermissionName,
    RoleName,
    UserId,
    Username,
)
from app.services.authorization_service import AuthorizationService


def make_identity(
    *,
    permissions: frozenset[PermissionName],
) -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        user_id=UserId(
            UUID("01900000-0000-7000-8000-000000000001")
        ),
        username=Username("nocadmin"),
        roles=frozenset(
            {
                RoleName("administrator"),
            }
        ),
        permissions=permissions,
    )


class FakeAuditRepository:
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
        self.records.append(
            (
                event_type,
                identity,
                details,
            )
        )


def test_authorize_accepts_granted_permission() -> None:
    identity = make_identity(
        permissions=frozenset(
            {
                PermissionName("dashboard.view"),
            }
        )
    )
    audit_repository = FakeAuditRepository()

    service = AuthorizationService(
        audit_repository=audit_repository,
    )

    result = service.authorize(
        identity=identity,
        permission="dashboard.view",
    )

    assert result is None
    assert audit_repository.records == [
        (
            "identity.authorization.succeeded",
            identity,
            {
                "permission": "dashboard.view",
            },
        )
    ]


def test_authorize_rejects_missing_permission() -> None:
    identity = make_identity(
        permissions=frozenset(
            {
                PermissionName("dashboard.view"),
            }
        )
    )
    audit_repository = FakeAuditRepository()

    service = AuthorizationService(
        audit_repository=audit_repository,
    )

    with pytest.raises(PermissionDenied):
        service.authorize(
            identity=identity,
            permission="users.manage",
        )

    assert audit_repository.records == [
        (
            "identity.authorization.denied",
            identity,
            {
                "permission": "users.manage",
            },
        )
    ]