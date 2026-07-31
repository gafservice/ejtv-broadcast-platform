"""Pruebas del catálogo oficial de Identity."""

from app.domain.identity.catalog import (
    ADMINISTRATOR_ROLE,
    ALL_PERMISSIONS,
    DEFAULT_ROLES,
    OPERATOR_ROLE,
    VIEWER_ROLE,
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


def test_default_roles_contains_expected_roles() -> None:
    assert {
        role.name.value
        for role in DEFAULT_ROLES
    } == {
        "administrator",
        "operator",
        "viewer",
    }


def test_catalog_uses_domain_value_objects() -> None:
    assert all(
        isinstance(permission, PermissionName)
        for permission in ALL_PERMISSIONS
    )

    assert all(
        isinstance(role.name, RoleName)
        for role in DEFAULT_ROLES
    )


def test_operator_role_has_expected_name() -> None:
    assert OPERATOR_ROLE.name == RoleName("operator")


def test_operator_role_has_expected_permissions() -> None:
    assert {
        permission.value
        for permission in OPERATOR_ROLE.permissions
    } == {
        "system.read",
        "dashboard.read",
        "streaming.read",
        "streaming.write",
        "alarms.read",
        "alarms.write",
    }


def test_viewer_role_has_expected_name() -> None:
    assert VIEWER_ROLE.name == RoleName("viewer")


def test_viewer_role_has_expected_permissions() -> None:
    assert {
        permission.value
        for permission in VIEWER_ROLE.permissions
    } == {
        "system.read",
        "dashboard.read",
        "streaming.read",
        "alarms.read",
    }


def test_default_role_names_are_unique() -> None:
    role_names = [
        role.name.value
        for role in DEFAULT_ROLES
    ]

    assert len(role_names) == len(set(role_names))


def test_default_role_permissions_belong_to_catalog() -> None:
    assert all(
        role.permissions <= ALL_PERMISSIONS
        for role in DEFAULT_ROLES
    )


def test_viewer_permissions_are_subset_of_operator() -> None:
    assert VIEWER_ROLE.permissions < OPERATOR_ROLE.permissions


def test_only_administrator_has_administrative_permissions() -> None:
    administrative_permissions = {
        "identity.read",
        "identity.write",
        "users.read",
        "users.write",
        "users.manage",
        "roles.read",
        "roles.write",
    }

    assert administrative_permissions <= {
        permission.value
        for permission in ADMINISTRATOR_ROLE.permissions
    }

    assert administrative_permissions.isdisjoint(
        {
            permission.value
            for permission in OPERATOR_ROLE.permissions
        }
    )

    assert administrative_permissions.isdisjoint(
        {
            permission.value
            for permission in VIEWER_ROLE.permissions
        }
    )

