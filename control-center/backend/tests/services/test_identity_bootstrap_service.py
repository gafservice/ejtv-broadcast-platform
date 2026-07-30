"""Tests for the Identity bootstrap application service."""

from collections.abc import Mapping

from app.domain.identity.entities import AuthenticatedIdentity, User
from app.domain.identity.value_objects import PasswordHash, Username
from app.services.identity_bootstrap_service import (
    BootstrapStatus,
    IdentityBootstrapService,
)


class FakeUserRepository:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.saved_users: list[User] = []

    def get_by_id(self, user_id):
        return next(
            (
                user
                for user in self.users.values()
                if user.id == user_id
            ),
            None,
        )

    def get_by_username(
        self,
        username: Username,
    ) -> User | None:
        return self.users.get(username.value)

    def save(self, user: User) -> None:
        self.users[user.username.value] = user
        self.saved_users.append(user)


class FakePasswordHasher:
    def __init__(self) -> None:
        self.hashed_passwords: list[str] = []

    def hash(self, plain_password: str) -> PasswordHash:
        self.hashed_passwords.append(plain_password)
        return PasswordHash("$2b$12$bootstrap_test_hash_value")

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
            (event_type, identity, details)
        )


def build_service():
    user_repository = FakeUserRepository()
    password_hasher = FakePasswordHasher()
    audit_repository = FakeAuditRepository()

    service = IdentityBootstrapService(
        user_repository=user_repository,
        password_hasher=password_hasher,
        audit_repository=audit_repository,
    )

    return (
        service,
        user_repository,
        password_hasher,
        audit_repository,
    )


def test_bootstrap_creates_administrator() -> None:
    (
        service,
        user_repository,
        password_hasher,
        audit_repository,
    ) = build_service()

    result = service.bootstrap_administrator(
        username="administrator",
        email="admin@example.com",
        password="ChangeMeNow123!",
    )

    assert result.status is BootstrapStatus.CREATED
    assert result.created is True
    assert result.user.username.value == "administrator"
    assert result.user.email.value == "admin@example.com"
    assert result.user.is_active()
    assert len(user_repository.saved_users) == 1
    assert password_hasher.hashed_passwords == [
        "ChangeMeNow123!"
    ]
    assert audit_repository.records[0][0] == (
        "identity.bootstrap.administrator_created"
    )


def test_bootstrap_assigns_administrator_role() -> None:
    service, _, _, _ = build_service()

    result = service.bootstrap_administrator(
        username="administrator",
        email="admin@example.com",
        password="ChangeMeNow123!",
    )

    role_names = {
        role.name.value
        for role in result.user.roles
    }

    assert role_names == {"administrator"}


def test_bootstrap_assigns_all_catalog_permissions() -> None:
    service, _, _, _ = build_service()

    result = service.bootstrap_administrator(
        username="administrator",
        email="admin@example.com",
        password="ChangeMeNow123!",
    )

    permissions = {
        permission.name.value
        for role in result.user.roles
        for permission in role.permissions
    }

    assert permissions == {
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


def test_bootstrap_is_idempotent() -> None:
    (
        service,
        user_repository,
        password_hasher,
        audit_repository,
    ) = build_service()

    first_result = service.bootstrap_administrator(
        username="administrator",
        email="admin@example.com",
        password="InitialPassword123!",
    )

    second_result = service.bootstrap_administrator(
        username="administrator",
        email="different@example.com",
        password="DifferentPassword123!",
    )

    assert first_result.status is BootstrapStatus.CREATED
    assert second_result.status is BootstrapStatus.ALREADY_EXISTS
    assert second_result.created is False
    assert second_result.user == first_result.user
    assert len(user_repository.saved_users) == 1
    assert password_hasher.hashed_passwords == [
        "InitialPassword123!"
    ]
    assert audit_repository.records[-1][0] == (
        "identity.bootstrap.skipped"
    )


def test_existing_user_is_not_modified() -> None:
    service, user_repository, _, _ = build_service()

    original_result = service.bootstrap_administrator(
        username="administrator",
        email="original@example.com",
        password="InitialPassword123!",
    )

    repeated_result = service.bootstrap_administrator(
        username="administrator",
        email="changed@example.com",
        password="ChangedPassword123!",
    )

    assert repeated_result.user.email.value == (
        "original@example.com"
    )
    assert (
        repeated_result.user.password_hash
        == original_result.user.password_hash
    )
    assert len(user_repository.saved_users) == 1


def test_created_audit_contains_identity_and_role() -> None:
    service, _, _, audit_repository = build_service()

    service.bootstrap_administrator(
        username="administrator",
        email="admin@example.com",
        password="ChangeMeNow123!",
    )

    event_type, identity, details = audit_repository.records[0]

    assert event_type == (
        "identity.bootstrap.administrator_created"
    )
    assert identity is not None
    assert identity.username.value == "administrator"
    assert details == {
        "username": "administrator",
        "role": "administrator",
    }
