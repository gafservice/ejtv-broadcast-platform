"""Tests for IdentityAdministrationService."""

from uuid import UUID

import pytest

from app.domain.identity.entities import (
    AuthenticatedIdentity,
    User,
)
from app.domain.identity.enums import UserStatus
from app.domain.identity.exceptions import (
    EmailAlreadyExists,
    UsernameAlreadyExists,
)
from app.domain.identity.value_objects import (
    Email,
    PasswordHash,
    PermissionName,
    RoleName,
    UserId,
    Username,
)
from app.services.identity_administration_service import (
    IdentityAdministrationService,
)


class FakeUserRepository:
    def __init__(self) -> None:
        self.users: dict[UserId, User] = {}

    def get_by_id(
        self,
        user_id: UserId,
    ) -> User | None:
        return self.users.get(user_id)

    def get_by_username(
        self,
        username: Username,
    ) -> User | None:
        return next(
            (
                user
                for user in self.users.values()
                if user.username == username
            ),
            None,
        )

    def get_by_email(
        self,
        email: Email,
    ) -> User | None:
        return next(
            (
                user
                for user in self.users.values()
                if user.email == email
            ),
            None,
        )

    def list(self) -> tuple[User, ...]:
        return tuple(
            sorted(
                self.users.values(),
                key=lambda user: user.username.value,
            )
        )

    def save(self, user: User) -> None:
        self.users[user.id] = user


class FakePasswordHasher:
    def __init__(self) -> None:
        self.received_password: str | None = None

    def hash(self, plain_password: str) -> PasswordHash:
        self.received_password = plain_password
        return PasswordHash(
            "$2b$12$zyxwvutsrqponmlkjihgfe"
            "zyxwvutsrqponmlkjihgfe1234567890"
        )

    def verify(
        self,
        plain_password: str,
        password_hash: PasswordHash,
    ) -> bool:
        return False


class FakeAuditRepository:
    def __init__(self) -> None:
        self.records: list[
            tuple[
                str,
                AuthenticatedIdentity | None,
                dict[str, object],
            ]
        ] = []

    def record(
        self,
        event_type: str,
        identity: AuthenticatedIdentity | None,
        details: dict[str, object],
    ) -> None:
        self.records.append(
            (
                event_type,
                identity,
                details,
            )
        )


def make_actor() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        user_id=UserId(
            UUID(
                "01900000-0000-7000-8000-000000000101"
            )
        ),
        username=Username("administrator"),
        roles=frozenset(
            {
                RoleName("administrator"),
            }
        ),
        permissions=frozenset(
            {
                PermissionName("users.read"),
                PermissionName("users.write"),
            }
        ),
    )


def make_user(
    *,
    user_id: str,
    username: str,
    email: str,
) -> User:
    return User(
        id=UserId(UUID(user_id)),
        username=Username(username),
        email=Email(email),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
    )


def build_service():
    repository = FakeUserRepository()
    hasher = FakePasswordHasher()
    audit = FakeAuditRepository()

    service = IdentityAdministrationService(
        user_repository=repository,
        password_hasher=hasher,
        audit_repository=audit,
    )

    return service, repository, hasher, audit


def test_create_user_persists_active_user() -> None:
    service, repository, hasher, audit = (
        build_service()
    )

    actor = make_actor()

    user = service.create_user(
        actor=actor,
        username="operator",
        email="operator@example.com",
        password="Secure-Password-2026!",
    )

    assert repository.get_by_id(user.id) == user
    assert user.username == Username("operator")
    assert user.email == Email("operator@example.com")
    assert user.roles == frozenset()
    assert user.is_active()
    assert hasher.received_password == "Secure-Password-2026!"

    assert audit.records[0][0] == (
        "identity.user.created"
    )
    assert audit.records[0][1] == actor
    assert audit.records[0][2][
        "target_username"
    ] == "operator"


def test_create_user_rejects_duplicate_username() -> None:
    service, repository, _, audit = build_service()

    existing = make_user(
        user_id=(
            "01900000-0000-7000-8000-000000000102"
        ),
        username="operator",
        email="first@example.com",
    )
    repository.save(existing)

    with pytest.raises(UsernameAlreadyExists):
        service.create_user(
            actor=make_actor(),
            username="operator",
            email="second@example.com",
            password="Secure-Password-2026!",
        )

    assert len(repository.list()) == 1
    assert audit.records == []


def test_create_user_rejects_duplicate_email() -> None:
    service, repository, _, audit = build_service()

    existing = make_user(
        user_id=(
            "01900000-0000-7000-8000-000000000103"
        ),
        username="first-user",
        email="shared@example.com",
    )
    repository.save(existing)

    with pytest.raises(EmailAlreadyExists):
        service.create_user(
            actor=make_actor(),
            username="second-user",
            email="shared@example.com",
            password="Secure-Password-2026!",
        )

    assert len(repository.list()) == 1
    assert audit.records == []


def test_list_users_returns_repository_order() -> None:
    service, repository, _, audit = build_service()

    repository.save(
        make_user(
            user_id=(
                "01900000-0000-7000-8000-000000000104"
            ),
            username="zeta-user",
            email="zeta@example.com",
        )
    )
    repository.save(
        make_user(
            user_id=(
                "01900000-0000-7000-8000-000000000105"
            ),
            username="alpha-user",
            email="alpha@example.com",
        )
    )

    actor = make_actor()
    users = service.list_users(actor=actor)

    assert [
        user.username.value
        for user in users
    ] == [
        "alpha-user",
        "zeta-user",
    ]

    assert audit.records == [
        (
            "identity.users.listed",
            actor,
            {"result_count": 2},
        )
    ]


@pytest.mark.parametrize(
    "method_name",
    [
        "create_user",
        "list_users",
    ],
)
def test_operations_reject_invalid_actor(
    method_name: str,
) -> None:
    service, _, _, _ = build_service()

    method = getattr(service, method_name)

    arguments: dict[str, object] = {
        "actor": object(),
    }

    if method_name == "create_user":
        arguments.update(
            {
                "username": "operator",
                "email": "operator@example.com",
                "password": "Secure-Password-2026!",
            }
        )

    with pytest.raises(TypeError):
        method(**arguments)


def test_get_user_returns_existing_user() -> None:
    service, repository, _, audit = build_service()

    user = make_user(
        user_id=(
            "01900000-0000-7000-8000-000000000106"
        ),
        username="operator",
        email="operator@example.com",
    )
    repository.save(user)

    actor = make_actor()

    restored = service.get_user(
        actor=actor,
        user_id=str(user.id),
    )

    assert restored == user
    assert audit.records == [
        (
            "identity.user.retrieved",
            actor,
            {
                "target_user_id": str(user.id),
                "target_username": "operator",
            },
        )
    ]


def test_get_user_raises_when_unknown() -> None:
    from app.domain.identity.exceptions import UserNotFound

    service, _, _, audit = build_service()

    with pytest.raises(UserNotFound):
        service.get_user(
            actor=make_actor(),
            user_id=(
                "01900000-0000-7000-8000-000000000199"
            ),
        )

    assert audit.records == []


def test_change_user_status_persists_update() -> None:
    from app.domain.identity.enums import UserStatus

    service, repository, _, audit = build_service()

    user = make_user(
        user_id=(
            "01900000-0000-7000-8000-000000000107"
        ),
        username="operator",
        email="operator@example.com",
    )
    repository.save(user)

    actor = make_actor()

    updated = service.change_user_status(
        actor=actor,
        user_id=str(user.id),
        status=UserStatus.DISABLED,
    )

    assert updated.status is UserStatus.DISABLED
    assert repository.get_by_id(user.id) == updated

    assert audit.records == [
        (
            "identity.user.status_changed",
            actor,
            {
                "target_user_id": str(user.id),
                "target_username": "operator",
                "previous_status": "active",
                "new_status": "disabled",
            },
        )
    ]


def test_change_user_status_rejects_invalid_status() -> None:
    service, _, _, audit = build_service()

    with pytest.raises(TypeError):
        service.change_user_status(
            actor=make_actor(),
            user_id=(
                "01900000-0000-7000-8000-000000000107"
            ),
            status="disabled",  # type: ignore[arg-type]
        )

    assert audit.records == []


def test_change_password_hashes_and_persists() -> None:
    service, repository, hasher, audit = build_service()

    user = make_user(
        user_id=(
            "01900000-0000-7000-8000-000000000108"
        ),
        username="operator",
        email="operator@example.com",
    )
    repository.save(user)

    actor = make_actor()

    updated = service.change_password(
        actor=actor,
        user_id=str(user.id),
        password="New-Secure-Password-2026!",
    )

    assert hasher.received_password == (
        "New-Secure-Password-2026!"
    )
    assert updated.password_hash != user.password_hash
    assert repository.get_by_id(user.id) == updated

    assert audit.records == [
        (
            "identity.user.password_changed",
            actor,
            {
                "target_user_id": str(user.id),
                "target_username": "operator",
            },
        )
    ]


@pytest.mark.parametrize(
    "method_name",
    [
        "get_user",
        "change_user_status",
        "change_password",
    ],
)
def test_new_operations_reject_invalid_actor(
    method_name: str,
) -> None:
    from app.domain.identity.enums import UserStatus

    service, _, _, _ = build_service()

    arguments: dict[str, object] = {
        "actor": object(),
        "user_id": (
            "01900000-0000-7000-8000-000000000109"
        ),
    }

    if method_name == "change_user_status":
        arguments["status"] = UserStatus.ACTIVE

    if method_name == "change_password":
        arguments["password"] = "Secure-Password-2026!"

    with pytest.raises(TypeError):
        getattr(service, method_name)(**arguments)


def test_list_roles_returns_canonical_roles() -> None:
    service, _, _, audit = build_service()
    actor = make_actor()

    roles = service.list_roles(actor=actor)

    assert [
        role.name.value
        for role in roles
    ] == [
        "administrator",
        "operator",
        "viewer",
    ]

    assert audit.records == [
        (
            "identity.roles.listed",
            actor,
            {"result_count": 3},
        )
    ]


def test_assign_role_persists_canonical_role() -> None:
    service, repository, _, audit = build_service()

    user = make_user(
        user_id=(
            "01900000-0000-7000-8000-000000000110"
        ),
        username="operator-user",
        email="operator-user@example.com",
    )
    repository.save(user)

    actor = make_actor()

    updated = service.assign_role(
        actor=actor,
        user_id=str(user.id),
        role_name="operator",
    )

    assert updated.has_role_name(
        RoleName("operator")
    )
    assert repository.get_by_id(user.id) == updated

    operator_role = next(
        role
        for role in updated.roles
        if role.name == RoleName("operator")
    )

    assert {
        permission.name.value
        for permission in operator_role.permissions
    } == {
        "system.read",
        "dashboard.read",
        "streaming.read",
        "streaming.write",
        "alarms.read",
        "alarms.write",
    }

    assert audit.records == [
        (
            "identity.user.role_assigned",
            actor,
            {
                "target_user_id": str(user.id),
                "target_username": "operator-user",
                "role": "operator",
                "changed": True,
            },
        )
    ]


def test_assign_role_is_idempotent() -> None:
    from app.domain.identity.entities import Permission, Role
    from app.domain.identity.value_objects import PermissionName

    service, repository, _, audit = build_service()

    operator_role = Role(
        name=RoleName("operator"),
        permissions=frozenset(
            {
                Permission(
                    name=PermissionName("system.read")
                )
            }
        ),
    )

    user = User(
        id=UserId(
            UUID(
                "01900000-0000-7000-8000-000000000111"
            )
        ),
        username=Username("existing-operator"),
        email=Email("existing-operator@example.com"),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
        roles=frozenset({operator_role}),
    )
    repository.save(user)

    actor = make_actor()

    updated = service.assign_role(
        actor=actor,
        user_id=str(user.id),
        role_name="operator",
    )

    assert updated is user
    assert repository.get_by_id(user.id) == user
    assert audit.records[0][2]["changed"] is False


def test_assign_role_rejects_unknown_role() -> None:
    from app.domain.identity.exceptions import RoleNotFound

    service, repository, _, audit = build_service()

    user = make_user(
        user_id=(
            "01900000-0000-7000-8000-000000000112"
        ),
        username="role-test",
        email="role-test@example.com",
    )
    repository.save(user)

    with pytest.raises(RoleNotFound):
        service.assign_role(
            actor=make_actor(),
            user_id=str(user.id),
            role_name="unknown_role",
        )

    assert audit.records == []


def test_remove_role_persists_updated_user() -> None:
    from app.domain.identity.entities import Role

    service, repository, _, audit = build_service()

    viewer_role = Role(
        name=RoleName("viewer"),
    )

    user = User(
        id=UserId(
            UUID(
                "01900000-0000-7000-8000-000000000113"
            )
        ),
        username=Username("viewer-user"),
        email=Email("viewer-user@example.com"),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
        roles=frozenset({viewer_role}),
    )
    repository.save(user)

    actor = make_actor()

    updated = service.remove_role(
        actor=actor,
        user_id=str(user.id),
        role_name="viewer",
    )

    assert not updated.has_role_name(
        RoleName("viewer")
    )
    assert repository.get_by_id(user.id) == updated

    assert audit.records == [
        (
            "identity.user.role_removed",
            actor,
            {
                "target_user_id": str(user.id),
                "target_username": "viewer-user",
                "role": "viewer",
                "changed": True,
            },
        )
    ]


def test_remove_role_is_idempotent() -> None:
    service, repository, _, audit = build_service()

    user = make_user(
        user_id=(
            "01900000-0000-7000-8000-000000000114"
        ),
        username="no-role-user",
        email="no-role-user@example.com",
    )
    repository.save(user)

    updated = service.remove_role(
        actor=make_actor(),
        user_id=str(user.id),
        role_name="viewer",
    )

    assert updated is user
    assert audit.records[0][2]["changed"] is False


def test_remove_last_administrator_is_rejected() -> None:
    from app.domain.identity.entities import Role
    from app.domain.identity.exceptions import (
        CannotRemoveLastAdministrator,
    )

    service, repository, _, audit = build_service()

    administrator_role = Role(
        name=RoleName("administrator"),
    )

    user = User(
        id=UserId(
            UUID(
                "01900000-0000-7000-8000-000000000115"
            )
        ),
        username=Username("sole-admin"),
        email=Email("sole-admin@example.com"),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
        roles=frozenset({administrator_role}),
    )
    repository.save(user)

    with pytest.raises(
        CannotRemoveLastAdministrator
    ):
        service.remove_role(
            actor=make_actor(),
            user_id=str(user.id),
            role_name="administrator",
        )

    assert repository.get_by_id(user.id) == user
    assert audit.records == []


def test_remove_administrator_when_another_exists() -> None:
    from app.domain.identity.entities import Role

    service, repository, _, _ = build_service()

    administrator_role = Role(
        name=RoleName("administrator"),
    )

    first = User(
        id=UserId(
            UUID(
                "01900000-0000-7000-8000-000000000116"
            )
        ),
        username=Username("first-admin"),
        email=Email("first-admin@example.com"),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
        roles=frozenset({administrator_role}),
    )

    second = User(
        id=UserId(
            UUID(
                "01900000-0000-7000-8000-000000000117"
            )
        ),
        username=Username("second-admin"),
        email=Email("second-admin@example.com"),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
        roles=frozenset({administrator_role}),
    )

    repository.save(first)
    repository.save(second)

    updated = service.remove_role(
        actor=make_actor(),
        user_id=str(first.id),
        role_name="administrator",
    )

    assert not updated.has_role_name(
        RoleName("administrator")
    )

    assert repository.get_by_id(
        second.id
    ).has_role_name(
        RoleName("administrator")
    )


@pytest.mark.parametrize(
    "method_name",
    [
        "list_roles",
        "assign_role",
        "remove_role",
    ],
)
def test_role_operations_reject_invalid_actor(
    method_name: str,
) -> None:
    service, _, _, _ = build_service()

    arguments: dict[str, object] = {
        "actor": object(),
    }

    if method_name != "list_roles":
        arguments.update(
            {
                "user_id": (
                    "01900000-0000-7000-8000-000000000118"
                ),
                "role_name": "viewer",
            }
        )

    with pytest.raises(TypeError):
        getattr(service, method_name)(**arguments)


def test_list_permissions_returns_canonical_permissions() -> None:
    service, _, _, audit = build_service()
    actor = make_actor()

    permissions = service.list_permissions(
        actor=actor
    )

    assert permissions == (
        "alarms.read",
        "alarms.write",
        "dashboard.read",
        "dashboard.write",
        "identity.read",
        "identity.write",
        "roles.read",
        "roles.write",
        "streaming.read",
        "streaming.write",
        "system.read",
        "system.write",
        "users.manage",
        "users.read",
        "users.write",
    )

    assert audit.records == [
        (
            "identity.permissions.listed",
            actor,
            {
                "result_count": 15,
            },
        )
    ]


def test_list_permissions_rejects_invalid_actor() -> None:
    service, _, _, _ = build_service()

    with pytest.raises(TypeError):
        service.list_permissions(
            actor=object()  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "status",
    [
        UserStatus.DISABLED,
        UserStatus.LOCKED,
    ],
)
def test_change_status_rejects_last_active_administrator(
    status: UserStatus,
) -> None:
    from app.domain.identity.entities import Role
    from app.domain.identity.exceptions import (
        CannotDisableLastAdministrator,
    )

    service, repository, _, audit = build_service()

    administrator_role = Role(
        name=RoleName("administrator"),
    )

    administrator = User(
        id=UserId(
            UUID(
                "01900000-0000-7000-8000-000000000301"
            )
        ),
        username=Username("sole-active-admin"),
        email=Email("sole-active-admin@example.com"),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
        roles=frozenset({administrator_role}),
        status=UserStatus.ACTIVE,
    )

    repository.save(administrator)

    with pytest.raises(
        CannotDisableLastAdministrator
    ):
        service.change_user_status(
            actor=make_actor(),
            user_id=str(administrator.id),
            status=status,
        )

    restored = repository.get_by_id(
        administrator.id
    )

    assert restored.status is UserStatus.ACTIVE
    assert audit.records == []


@pytest.mark.parametrize(
    "status",
    [
        UserStatus.DISABLED,
        UserStatus.LOCKED,
    ],
)
def test_change_status_allows_administrator_when_another_active_exists(
    status: UserStatus,
) -> None:
    from app.domain.identity.entities import Role

    service, repository, _, audit = build_service()

    administrator_role = Role(
        name=RoleName("administrator"),
    )

    first = User(
        id=UserId(
            UUID(
                "01900000-0000-7000-8000-000000000302"
            )
        ),
        username=Username("first-active-admin"),
        email=Email("first-active-admin@example.com"),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
        roles=frozenset({administrator_role}),
        status=UserStatus.ACTIVE,
    )

    second = User(
        id=UserId(
            UUID(
                "01900000-0000-7000-8000-000000000303"
            )
        ),
        username=Username("second-active-admin"),
        email=Email("second-active-admin@example.com"),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
        roles=frozenset({administrator_role}),
        status=UserStatus.ACTIVE,
    )

    repository.save(first)
    repository.save(second)
    audit.records.clear()

    updated = service.change_user_status(
        actor=make_actor(),
        user_id=str(first.id),
        status=status,
    )

    assert updated.status is status

    restored_second = repository.get_by_id(
        second.id
    )

    assert restored_second.is_active()
    assert restored_second.has_role_name(
        RoleName("administrator")
    )

    assert audit.records[0][0] == (
        "identity.user.status_changed"
    )


def test_inactive_administrator_does_not_count_as_backup() -> None:
    from app.domain.identity.entities import Role
    from app.domain.identity.exceptions import (
        CannotDisableLastAdministrator,
    )

    service, repository, _, audit = build_service()

    administrator_role = Role(
        name=RoleName("administrator"),
    )

    active_administrator = User(
        id=UserId(
            UUID(
                "01900000-0000-7000-8000-000000000304"
            )
        ),
        username=Username("active-admin"),
        email=Email("active-admin@example.com"),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
        roles=frozenset({administrator_role}),
        status=UserStatus.ACTIVE,
    )

    disabled_administrator = User(
        id=UserId(
            UUID(
                "01900000-0000-7000-8000-000000000305"
            )
        ),
        username=Username("disabled-admin"),
        email=Email("disabled-admin@example.com"),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
        roles=frozenset({administrator_role}),
        status=UserStatus.DISABLED,
    )

    repository.save(active_administrator)
    repository.save(disabled_administrator)
    audit.records.clear()

    with pytest.raises(
        CannotDisableLastAdministrator
    ):
        service.change_user_status(
            actor=make_actor(),
            user_id=str(active_administrator.id),
            status=UserStatus.LOCKED,
        )

    assert audit.records == []


@pytest.mark.parametrize(
    "password",
    [
        "short",
        "lowercase-password-2026!",
        "UPPERCASE-PASSWORD-2026!",
        "PasswordWithoutNumber!",
        "PasswordWithoutSymbol2026",
    ],
)
def test_create_user_rejects_weak_password(
    password: str,
) -> None:
    from app.domain.identity.exceptions import WeakPassword

    service, repository, hasher, audit = build_service()

    with pytest.raises(WeakPassword):
        service.create_user(
            actor=make_actor(),
            username="weak-password-user",
            email="weak-password@example.com",
            password=password,
        )

    assert repository.list() == ()
    assert audit.records == []


def test_change_password_rejects_weak_password() -> None:
    from app.domain.identity.exceptions import WeakPassword

    service, repository, hasher, audit = build_service()
    user = make_user(
        user_id="01900000-0000-7000-8000-000000000999",
        username="operator",
        email="operator@example.com",
    )

    repository.save(user)
    audit.records.clear()

    with pytest.raises(WeakPassword):
        service.change_password(
            actor=make_actor(),
            user_id=str(user.id),
            password="weak",
        )

    restored = repository.get_by_id(user.id)

    assert restored.password_hash == user.password_hash
    assert audit.records == []
