from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from app.domain.identity.entities import Permission, Role, User
from app.domain.identity.enums import UserStatus
from app.domain.identity.value_objects import (
    Email,
    PasswordHash,
    PermissionName,
    RoleName,
    UserId,
    Username,
)


def make_permission(name: str = "dashboard.view") -> Permission:
    return Permission(PermissionName(name))


def make_role(
    name: str = "observer",
    permissions: frozenset[Permission] | None = None,
) -> Role:
    return Role(
        name=RoleName(name),
        permissions=permissions or frozenset(),
    )


def make_user(
    *,
    roles: frozenset[Role] | None = None,
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
    return User(
        id=UserId(
            UUID("01900000-0000-7000-8000-000000000001")
        ),
        username=Username("nocadmin"),
        email=Email("nocadmin@example.com"),
        password_hash=PasswordHash(
            "$argon2id$v=19$m=65536,t=3,p=4$"
            "c29tZXNhbHQ$"
            "c29tZXZhbGlkaGFzaHZhbHVl"
        ),
        roles=roles or frozenset(),
        status=status,
    )


def test_user_accepts_valid_identity_data() -> None:
    role = make_role()

    user = make_user(roles=frozenset({role}))

    assert str(user.username) == "nocadmin"
    assert str(user.email) == "nocadmin@example.com"
    assert user.roles == frozenset({role})
    assert user.status is UserStatus.ACTIVE


def test_user_defaults_to_empty_roles() -> None:
    user = make_user()

    assert user.roles == frozenset()


def test_user_is_immutable() -> None:
    user = make_user()

    with pytest.raises(FrozenInstanceError):
        user.status = UserStatus.LOCKED  # type: ignore[misc]


def test_user_roles_collection_is_immutable() -> None:
    user = make_user(roles=frozenset({make_role()}))

    assert isinstance(user.roles, frozenset)


def test_user_removes_duplicate_roles() -> None:
    role = make_role()

    user = make_user(roles=frozenset({role, role}))

    assert user.roles == frozenset({role})


def test_user_is_active_returns_true_for_active_user() -> None:
    user = make_user(status=UserStatus.ACTIVE)

    assert user.is_active() is True


def test_user_is_active_returns_false_for_disabled_user() -> None:
    user = make_user(status=UserStatus.DISABLED)

    assert user.is_active() is False


def test_user_is_locked_returns_true_for_locked_user() -> None:
    user = make_user(status=UserStatus.LOCKED)

    assert user.is_locked() is True


def test_user_is_locked_returns_false_for_active_user() -> None:
    user = make_user(status=UserStatus.ACTIVE)

    assert user.is_locked() is False


def test_user_has_role_returns_true() -> None:
    role = make_role()
    user = make_user(roles=frozenset({role}))

    assert user.has_role(role) is True


def test_user_has_role_returns_false() -> None:
    user = make_user(roles=frozenset({make_role("observer")}))

    assert user.has_role(make_role("operator")) is False


def test_user_has_role_name_returns_true() -> None:
    user = make_user(roles=frozenset({make_role("operator")}))

    assert user.has_role_name(RoleName("operator")) is True


def test_user_has_role_name_returns_false() -> None:
    user = make_user(roles=frozenset({make_role("observer")}))

    assert user.has_role_name(RoleName("operator")) is False


def test_user_has_permission_returns_true() -> None:
    permission = make_permission("dashboard.view")
    role = make_role(
        permissions=frozenset({permission}),
    )
    user = make_user(roles=frozenset({role}))

    assert user.has_permission(permission) is True


def test_user_has_permission_returns_false() -> None:
    user = make_user(
        roles=frozenset(
            {
                make_role(
                    permissions=frozenset(
                        {make_permission("dashboard.view")}
                    )
                )
            }
        )
    )

    assert user.has_permission(
        make_permission("system.config.update")
    ) is False


def test_user_has_permission_name_returns_true() -> None:
    permission = make_permission("dashboard.view")
    role = make_role(permissions=frozenset({permission}))
    user = make_user(roles=frozenset({role}))

    assert user.has_permission_name(
        PermissionName("dashboard.view")
    ) is True


def test_user_has_permission_name_returns_false() -> None:
    user = make_user()

    assert user.has_permission_name(
        PermissionName("dashboard.view")
    ) is False


def test_with_status_returns_updated_user() -> None:
    user = make_user()

    updated = user.with_status(UserStatus.DISABLED)

    assert updated is not user
    assert updated.id == user.id
    assert updated.username == user.username
    assert updated.email == user.email
    assert updated.password_hash == user.password_hash
    assert updated.roles == user.roles
    assert updated.status is UserStatus.DISABLED

    assert user.status is UserStatus.ACTIVE


def test_with_status_accepts_locked_status() -> None:
    user = make_user()

    updated = user.with_status(UserStatus.LOCKED)

    assert updated.status is UserStatus.LOCKED
    assert updated.is_locked()


def test_with_status_rejects_invalid_value() -> None:
    user = make_user()

    with pytest.raises(TypeError):
        user.with_status("disabled")  # type: ignore[arg-type]


def test_with_password_hash_returns_updated_user() -> None:
    user = make_user()

    new_hash = PasswordHash(
        "$2b$12$zyxwvutsrqponmlkjihgfe"
        "zyxwvutsrqponmlkjihgfe1234567890"
    )

    updated = user.with_password_hash(new_hash)

    assert updated is not user
    assert updated.id == user.id
    assert updated.username == user.username
    assert updated.email == user.email
    assert updated.roles == user.roles
    assert updated.status == user.status
    assert updated.password_hash == new_hash

    assert user.password_hash != new_hash


def test_with_password_hash_rejects_invalid_value() -> None:
    user = make_user()

    with pytest.raises(TypeError):
        user.with_password_hash(
            "not-a-password-hash"  # type: ignore[arg-type]
        )
