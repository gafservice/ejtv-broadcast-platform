from dataclasses import FrozenInstanceError

import pytest

from app.domain.identity.entities import Permission, Role
from app.domain.identity.value_objects import (
    PermissionName,
    RoleName,
)


def make_permission(name: str) -> Permission:
    return Permission(
        name=PermissionName(name)
    )


def test_role_accepts_name_and_permissions() -> None:
    permissions = frozenset(
        {
            make_permission("stream.read"),
            make_permission("stream.publish"),
        }
    )

    role = Role(
        name=RoleName("operator"),
        permissions=permissions,
    )

    assert role.name == RoleName("operator")
    assert role.permissions == permissions


def test_role_defaults_to_empty_permissions() -> None:
    role = Role(
        name=RoleName("viewer")
    )

    assert role.permissions == frozenset()


def test_role_string_representation() -> None:
    role = Role(
        name=RoleName("administrator")
    )

    assert str(role) == "administrator"


def test_role_has_permission_returns_true() -> None:
    permission = make_permission("dashboard.view")

    role = Role(
        name=RoleName("viewer"),
        permissions=frozenset({permission}),
    )

    assert role.has_permission(permission) is True


def test_role_has_permission_returns_false() -> None:
    role = Role(
        name=RoleName("viewer"),
        permissions=frozenset(
            {
                make_permission("dashboard.view"),
            }
        ),
    )

    assert (
        role.has_permission(
            make_permission("stream.publish")
        )
        is False
    )


def test_role_has_permission_name_returns_true() -> None:
    role = Role(
        name=RoleName("operator"),
        permissions=frozenset(
            {
                make_permission("stream.read"),
                make_permission("stream.publish"),
            }
        ),
    )

    assert (
        role.has_permission_name(
            PermissionName("stream.publish")
        )
        is True
    )


def test_role_has_permission_name_returns_false() -> None:
    role = Role(
        name=RoleName("operator"),
        permissions=frozenset(
            {
                make_permission("stream.read"),
            }
        ),
    )

    assert (
        role.has_permission_name(
            PermissionName("system.metrics.read")
        )
        is False
    )


def test_role_removes_duplicate_permissions() -> None:
    permission = make_permission("stream.read")

    role = Role(
        name=RoleName("operator"),
        permissions=frozenset(
            {
                permission,
                permission,
            }
        ),
    )

    assert len(role.permissions) == 1


def test_role_equality_is_based_on_value() -> None:
    permissions = frozenset(
        {
            make_permission("stream.read"),
            make_permission("stream.publish"),
        }
    )

    left = Role(
        name=RoleName("operator"),
        permissions=permissions,
    )

    right = Role(
        name=RoleName("operator"),
        permissions=permissions,
    )

    assert left == right


def test_roles_with_different_permissions_are_not_equal() -> None:
    left = Role(
        name=RoleName("operator"),
        permissions=frozenset(
            {
                make_permission("stream.read"),
            }
        ),
    )

    right = Role(
        name=RoleName("operator"),
        permissions=frozenset(
            {
                make_permission("stream.publish"),
            }
        ),
    )

    assert left != right


def test_role_is_hashable() -> None:
    role = Role(
        name=RoleName("viewer"),
        permissions=frozenset(
            {
                make_permission("dashboard.view"),
            }
        ),
    )

    roles = {role}

    assert role in roles


def test_role_is_immutable() -> None:
    role = Role(
        name=RoleName("viewer")
    )

    with pytest.raises(FrozenInstanceError):
        role.name = RoleName(
            "operator"
        )  # type: ignore[misc]


def test_role_permissions_collection_is_immutable() -> None:
    role = Role(
        name=RoleName("viewer"),
        permissions=frozenset(
            {
                make_permission("dashboard.view"),
            }
        ),
    )

    with pytest.raises(AttributeError):
        role.permissions.add(
            make_permission("stream.read")
        )  # type: ignore[attr-defined]
