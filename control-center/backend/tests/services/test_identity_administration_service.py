"""Tests for IdentityAdministrationService."""

from uuid import UUID

import pytest

from app.domain.identity.entities import (
    AuthenticatedIdentity,
    User,
)
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
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
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
        password="secure-password",
    )

    assert repository.get_by_id(user.id) == user
    assert user.username == Username("operator")
    assert user.email == Email("operator@example.com")
    assert user.roles == frozenset()
    assert user.is_active()
    assert hasher.received_password == "secure-password"

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
            password="secure-password",
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
            password="secure-password",
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
                "password": "secure-password",
            }
        )

    with pytest.raises(TypeError):
        method(**arguments)
