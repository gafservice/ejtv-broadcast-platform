from dataclasses import FrozenInstanceError

import pytest

from app.domain.identity.entities import Permission
from app.domain.identity.value_objects import PermissionName


def test_permission_accepts_valid_permission_name() -> None:
    permission = Permission(
        name=PermissionName("stream.read")
    )

    assert permission.name == PermissionName("stream.read")


def test_permission_string_representation() -> None:
    permission = Permission(
        name=PermissionName("dashboard.view")
    )

    assert str(permission) == "dashboard.view"


def test_permission_equality_is_based_on_value() -> None:
    left = Permission(
        name=PermissionName("stream.read")
    )

    right = Permission(
        name=PermissionName("stream.read")
    )

    assert left == right


def test_permission_inequality() -> None:
    left = Permission(
        name=PermissionName("stream.read")
    )

    right = Permission(
        name=PermissionName("stream.publish")
    )

    assert left != right


def test_permission_is_hashable() -> None:
    permissions = {
        Permission(
            name=PermissionName("stream.read")
        )
    }

    assert Permission(
        name=PermissionName("stream.read")
    ) in permissions


def test_permission_is_immutable() -> None:
    permission = Permission(
        name=PermissionName("stream.read")
    )

    with pytest.raises(FrozenInstanceError):
        permission.name = PermissionName(
            "stream.publish"
        )  # type: ignore[misc]


def test_permission_can_be_used_as_dictionary_key() -> None:
    permission = Permission(
        name=PermissionName("dashboard.view")
    )

    mapping = {
        permission: "allowed",
    }

    assert (
        mapping[
            Permission(
                name=PermissionName("dashboard.view")
            )
        ]
        == "allowed"
    )
