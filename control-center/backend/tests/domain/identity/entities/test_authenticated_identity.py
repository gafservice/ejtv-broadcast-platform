from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from app.domain.identity.entities import (
    AuthenticatedIdentity,
    Permission,
    Role,
    User,
)
from app.domain.identity.value_objects import (
    Email,
    PasswordHash,
    PermissionName,
    RoleName,
    UserId,
    Username,
)


def make_user_id() -> UserId:
    return UserId(
        UUID("01900000-0000-7000-8000-000000000001")
    )


def make_identity() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        user_id=make_user_id(),
        username=Username("operator"),
        roles=frozenset(
            {
                RoleName("administrator"),
                RoleName("operator"),
            }
        ),
        permissions=frozenset(
            {
                PermissionName("dashboard.read"),
                PermissionName("streams.manage"),
            }
        ),
    )


def test_authenticated_identity_can_be_created() -> None:
    identity = make_identity()

    assert identity.user_id == make_user_id()
    assert identity.username == Username("operator")


def test_authenticated_identity_has_empty_roles_by_default() -> None:
    identity = AuthenticatedIdentity(
        user_id=make_user_id(),
        username=Username("operator"),
    )

    assert identity.roles == frozenset()


def test_authenticated_identity_has_empty_permissions_by_default() -> None:
    identity = AuthenticatedIdentity(
        user_id=make_user_id(),
        username=Username("operator"),
    )

    assert identity.permissions == frozenset()


def test_authenticated_identity_converts_roles_to_frozenset() -> None:
    identity = AuthenticatedIdentity(
        user_id=make_user_id(),
        username=Username("operator"),
        roles=[
            RoleName("administrator"),
            RoleName("operator"),
        ],
    )

    assert isinstance(identity.roles, frozenset)


def test_authenticated_identity_converts_permissions_to_frozenset() -> None:
    identity = AuthenticatedIdentity(
        user_id=make_user_id(),
        username=Username("operator"),
        permissions=[
            PermissionName("dashboard.read"),
            PermissionName("streams.manage"),
        ],
    )

    assert isinstance(identity.permissions, frozenset)


def test_authenticated_identity_is_immutable() -> None:
    identity = make_identity()

    with pytest.raises(FrozenInstanceError):
        identity.username = Username("changed")  # type: ignore[misc]


def test_authenticated_identity_is_hashable() -> None:
    identity = make_identity()

    assert identity in {identity}


def test_has_role_returns_true_for_assigned_role() -> None:
    identity = make_identity()

    assert identity.has_role(RoleName("administrator"))


def test_has_role_returns_false_for_unassigned_role() -> None:
    identity = make_identity()

    assert not identity.has_role(RoleName("viewer"))


def test_has_permission_returns_true_for_assigned_permission() -> None:
    identity = make_identity()

    assert identity.has_permission(
        PermissionName("dashboard.read")
    )


def test_has_permission_returns_false_for_unassigned_permission() -> None:
    identity = make_identity()

    assert not identity.has_permission(
        PermissionName("users.delete")
    )


def test_from_user_projects_user_identity() -> None:
    user = User(
        id=make_user_id(),
        username=Username("operator"),
        email=Email("operator@example.com"),
        password_hash=PasswordHash(
            "$argon2id$v=19$m=65536,t=3,p=4$"
            "c2FsdHNhbHRzYWx0c2FsdA$"
            "aGFzaGhhc2hoYXNoaGFzaGhhc2hoYXNo"
        ),
    )

    identity = AuthenticatedIdentity.from_user(user)

    assert identity.user_id == user.id
    assert identity.username == user.username


def test_from_user_projects_role_names() -> None:
    administrator = Role(
        name=RoleName("administrator")
    )
    operator = Role(
        name=RoleName("operator")
    )

    user = User(
        id=make_user_id(),
        username=Username("operator"),
        email=Email("operator@example.com"),
        password_hash=PasswordHash(
            "$argon2id$v=19$m=65536,t=3,p=4$"
            "c2FsdHNhbHRzYWx0c2FsdA$"
            "aGFzaGhhc2hoYXNoaGFzaGhhc2hoYXNo"
        ),
        roles=frozenset({administrator, operator}),
    )

    identity = AuthenticatedIdentity.from_user(user)

    assert identity.roles == frozenset(
        {
            RoleName("administrator"),
            RoleName("operator"),
        }
    )


def test_from_user_projects_effective_permissions() -> None:
    dashboard_read = Permission(
        PermissionName("dashboard.read")
    )
    streams_manage = Permission(
        PermissionName("streams.manage")
    )

    administrator = Role(
        name=RoleName("administrator"),
        permissions=frozenset(
            {dashboard_read, streams_manage}
        ),
    )

    user = User(
        id=make_user_id(),
        username=Username("operator"),
        email=Email("operator@example.com"),
        password_hash=PasswordHash(
            "$argon2id$v=19$m=65536,t=3,p=4$"
            "c2FsdHNhbHRzYWx0c2FsdA$"
            "aGFzaGhhc2hoYXNoaGFzaGhhc2hoYXNo"
        ),
        roles=frozenset({administrator}),
    )

    identity = AuthenticatedIdentity.from_user(user)

    assert identity.permissions == frozenset(
        {
            PermissionName("dashboard.read"),
            PermissionName("streams.manage"),
        }
    )


def test_from_user_removes_duplicate_effective_permissions() -> None:
    dashboard_read = Permission(
        PermissionName("dashboard.read")
    )

    administrator = Role(
        name=RoleName("administrator"),
        permissions=frozenset({dashboard_read}),
    )
    operator = Role(
        name=RoleName("operator"),
        permissions=frozenset({dashboard_read}),
    )

    user = User(
        id=make_user_id(),
        username=Username("operator"),
        email=Email("operator@example.com"),
        password_hash=PasswordHash(
            "$argon2id$v=19$m=65536,t=3,p=4$"
            "c2FsdHNhbHRzYWx0c2FsdA$"
            "aGFzaGhhc2hoYXNoaGFzaGhhc2hoYXNo"
        ),
        roles=frozenset({administrator, operator}),
    )

    identity = AuthenticatedIdentity.from_user(user)

    assert identity.permissions == frozenset(
        {PermissionName("dashboard.read")}
    )


def test_from_user_does_not_expose_sensitive_user_data() -> None:
    identity_fields = set(
        AuthenticatedIdentity.__dataclass_fields__
    )

    assert "password_hash" not in identity_fields
    assert "email" not in identity_fields
    assert "status" not in identity_fields
    assert "token" not in identity_fields
