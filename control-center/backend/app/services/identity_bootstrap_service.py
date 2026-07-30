"""Application service for bootstrapping the Identity subsystem."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.identity.catalog import ADMINISTRATOR_ROLE
from app.domain.identity.entities import (
    AuthenticatedIdentity,
    Permission,
    Role,
    User,
)
from app.domain.identity.protocols import (
    AuditRepository,
    PasswordHasher,
    UserRepository,
)
from app.domain.identity.value_objects import (
    Email,
    UserId,
    Username,
)


class BootstrapStatus(StrEnum):
    """Possible outcomes of an Identity bootstrap execution."""

    CREATED = "created"
    ALREADY_EXISTS = "already_exists"


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    """Result returned by the Identity bootstrap process."""

    status: BootstrapStatus
    user: User

    @property
    def created(self) -> bool:
        """Return whether the administrator was created."""

        return self.status is BootstrapStatus.CREATED


class IdentityBootstrapService:
    """Create the initial administrator account when it does not exist."""

    def __init__(
        self,
        *,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        audit_repository: AuditRepository,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._audit_repository = audit_repository

    def bootstrap_administrator(
        self,
        *,
        username: str,
        email: str,
        password: str,
    ) -> BootstrapResult:
        """
        Create the initial administrator account.

        Repeated executions are idempotent: an existing username is returned
        without changing its password, email, roles or status.
        """

        username_value = Username(username)

        existing_user = self._user_repository.get_by_username(
            username_value
        )

        if existing_user is not None:
            self._audit_repository.record(
                "identity.bootstrap.skipped",
                AuthenticatedIdentity.from_user(existing_user),
                {
                    "username": existing_user.username.value,
                    "reason": "administrator_already_exists",
                },
            )

            return BootstrapResult(
                status=BootstrapStatus.ALREADY_EXISTS,
                user=existing_user,
            )

        administrator_role = self._build_administrator_role()

        user = User(
            id=UserId.generate(),
            username=username_value,
            email=Email(email),
            password_hash=self._password_hasher.hash(password),
            roles=frozenset({administrator_role}),
        )

        self._user_repository.save(user)

        self._audit_repository.record(
            "identity.bootstrap.administrator_created",
            AuthenticatedIdentity.from_user(user),
            {
                "username": user.username.value,
                "role": administrator_role.name.value,
            },
        )

        return BootstrapResult(
            status=BootstrapStatus.CREATED,
            user=user,
        )

    @staticmethod
    def _build_administrator_role() -> Role:
        """Build the administrator role from the canonical catalog."""

        permissions = frozenset(
            Permission(name=permission_name)
            for permission_name in ADMINISTRATOR_ROLE.permissions
        )

        return Role(
            name=ADMINISTRATOR_ROLE.name,
            permissions=permissions,
        )
