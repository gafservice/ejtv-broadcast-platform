"""Pruebas del catálogo oficial de Identity."""

from app.domain.identity.catalog import (
    ADMINISTRATOR_ROLE,
    ALL_PERMISSIONS,
    DEFAULT_ROLES,
)
from app.domain.identity.value_objects import PermissionName, RoleName


def test_catalog_contains_expected_permissions() -> None:
    expected = {
        "system.read",
        "system.write",
        "dashboard.read",
        "dashboard.write",
        "streaming.read",
        "streaming.write",
        "identity.read",
        "identity.write",
        "users.read",
        "users.write",
        "users.manage",
        "roles.read",
        "roles.write",
        "alarms.read",
        "alarms.write",
    }

    assert {permission.value for permission in ALL_PERMISSIONS} == expected


def test_catalog_permissions_are_unique() -> None:
    values = [permission.value for permission in ALL_PERMISSIONS]

    assert len(values) == len(set(values))


def test_administrator_role_has_expected_name() -> None:
    assert ADMINISTRATOR_ROLE.name == RoleName("administrator")


def test_administrator_role_contains_all_permissions() -> None:
    assert ADMINISTRATOR_ROLE.permissions == ALL_PERMISSIONS


def test_default_roles_contains_administrator() -> None:
    assert ADMINISTRATOR_ROLE in DEFAULT_ROLES


def test_catalog_uses_domain_value_objects() -> None:
    assert all(
        isinstance(permission, PermissionName)
        for permission in ALL_PERMISSIONS
    )

    assert all(
        isinstance(role.name, RoleName)
        for role in DEFAULT_ROLES
    )
