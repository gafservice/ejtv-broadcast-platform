from collections.abc import Mapping
from uuid import UUID

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
from app.services.authentication_service import AuthenticationService


PASSWORD_HASH = PasswordHash(
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "c2FsdHNhbHRzYWx0c2FsdA$"
    "aGFzaGhhc2hoYXNoaGFzaGhhc2hoYXNo"
)


def make_user() -> User:
    permission = Permission(
        PermissionName("dashboard.view")
    )

    role = Role(
        name=RoleName("administrator"),
        permissions=frozenset({permission}),
    )

    return User(
        id=UserId(
            UUID("01900000-0000-7000-8000-000000000001")
        ),
        username=Username("nocadmin"),
        email=Email("nocadmin@example.com"),
        password_hash=PASSWORD_HASH,
        roles=frozenset({role}),
    )


class FakeUserRepository:
    def __init__(self, user: User) -> None:
        self.user = user
        self.requested_username: Username | None = None

    def get_by_id(
        self,
        user_id: UserId,
    ) -> User | None:
        if self.user.id == user_id:
            return self.user

        return None

    def get_by_username(
        self,
        username: Username,
    ) -> User | None:
        self.requested_username = username
        return self.user

    def save(self, user: User) -> None:
        self.user = user


class FakePasswordHasher:
    def __init__(self) -> None:
        self.received_plain_password: str | None = None
        self.received_password_hash: PasswordHash | None = None

    def hash(self, plain_password: str) -> PasswordHash:
        return PASSWORD_HASH

    def verify(
        self,
        plain_password: str,
        password_hash: PasswordHash,
    ) -> bool:
        self.received_plain_password = plain_password
        self.received_password_hash = password_hash
        return True


class FakeTokenProvider:
    def __init__(self) -> None:
        self.received_identity: AuthenticatedIdentity | None = None

    def issue(
        self,
        identity: AuthenticatedIdentity,
    ) -> str:
        self.received_identity = identity
        return "issued-access-token"

    def verify(
        self,
        token: str,
    ) -> AuthenticatedIdentity | None:
        return None


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


def test_authenticate_returns_token_for_valid_credentials() -> None:
    user = make_user()
    user_repository = FakeUserRepository(user)
    password_hasher = FakePasswordHasher()
    token_provider = FakeTokenProvider()
    audit_repository = FakeAuditRepository()

    service = AuthenticationService(
        user_repository=user_repository,
        password_hasher=password_hasher,
        token_provider=token_provider,
        audit_repository=audit_repository,
    )

    token = service.authenticate(
        username="nocadmin",
        password="correct-password",
    )

    identity = AuthenticatedIdentity.from_user(user)

    assert token == "issued-access-token"
    assert user_repository.requested_username == Username(
        "nocadmin"
    )
    assert (
        password_hasher.received_plain_password
        == "correct-password"
    )
    assert (
        password_hasher.received_password_hash
        == user.password_hash
    )
    assert token_provider.received_identity == identity
    assert audit_repository.records == [
        (
            "identity.login.succeeded",
            identity,
            {"username": "nocadmin"},
        )
    ]


from dataclasses import replace

import pytest

from app.domain.identity.exceptions import (
    InvalidCredentials,
    UserDisabled,
    UserLocked,
)
from app.domain.identity.enums import UserStatus


class MissingUserRepository(FakeUserRepository):
    def get_by_username(
        self,
        username: Username,
    ) -> User | None:
        self.requested_username = username
        return None


class RejectingPasswordHasher(FakePasswordHasher):
    def verify(
        self,
        plain_password: str,
        password_hash: PasswordHash,
    ) -> bool:
        self.received_plain_password = plain_password
        self.received_password_hash = password_hash
        return False


def test_authenticate_rejects_unknown_user() -> None:
    user_repository = MissingUserRepository(make_user())
    password_hasher = FakePasswordHasher()
    token_provider = FakeTokenProvider()
    audit_repository = FakeAuditRepository()

    service = AuthenticationService(
        user_repository=user_repository,
        password_hasher=password_hasher,
        token_provider=token_provider,
        audit_repository=audit_repository,
    )

    with pytest.raises(InvalidCredentials):
        service.authenticate(
            username="unknown-user",
            password="some-password",
        )

    assert user_repository.requested_username == Username(
        "unknown-user"
    )
    assert password_hasher.received_plain_password is None
    assert token_provider.received_identity is None
    assert audit_repository.records == []


def test_authenticate_rejects_invalid_password() -> None:
    user = make_user()
    user_repository = FakeUserRepository(user)
    password_hasher = RejectingPasswordHasher()
    token_provider = FakeTokenProvider()
    audit_repository = FakeAuditRepository()

    service = AuthenticationService(
        user_repository=user_repository,
        password_hasher=password_hasher,
        token_provider=token_provider,
        audit_repository=audit_repository,
    )

    with pytest.raises(InvalidCredentials):
        service.authenticate(
            username="nocadmin",
            password="wrong-password",
        )

    assert (
        password_hasher.received_plain_password
        == "wrong-password"
    )
    assert (
        password_hasher.received_password_hash
        == user.password_hash
    )
    assert token_provider.received_identity is None
    assert audit_repository.records == []


def test_authenticate_rejects_disabled_user() -> None:
    user = replace(
        make_user(),
        status=UserStatus.DISABLED,
    )

    user_repository = FakeUserRepository(user)
    password_hasher = FakePasswordHasher()
    token_provider = FakeTokenProvider()
    audit_repository = FakeAuditRepository()

    service = AuthenticationService(
        user_repository=user_repository,
        password_hasher=password_hasher,
        token_provider=token_provider,
        audit_repository=audit_repository,
    )

    with pytest.raises(UserDisabled):
        service.authenticate(
            username="nocadmin",
            password="correct-password",
        )

    assert password_hasher.received_plain_password is None
    assert token_provider.received_identity is None
    assert audit_repository.records == []


def test_authenticate_rejects_locked_user() -> None:
    user = replace(
        make_user(),
        status=UserStatus.LOCKED,
    )

    user_repository = FakeUserRepository(user)
    password_hasher = FakePasswordHasher()
    token_provider = FakeTokenProvider()
    audit_repository = FakeAuditRepository()

    service = AuthenticationService(
        user_repository=user_repository,
        password_hasher=password_hasher,
        token_provider=token_provider,
        audit_repository=audit_repository,
    )

    with pytest.raises(UserLocked):
        service.authenticate(
            username="nocadmin",
            password="correct-password",
        )

    assert password_hasher.received_plain_password is None
    assert token_provider.received_identity is None
    assert audit_repository.records == []
