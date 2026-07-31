"""Application service for Identity user administration."""

from __future__ import annotations

from app.domain.identity.entities import (
    AuthenticatedIdentity,
    User,
)
from app.domain.identity.exceptions import (
    EmailAlreadyExists,
    UsernameAlreadyExists,
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


class IdentityAdministrationService:
    """Coordinate administrative Identity user operations."""

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

    def create_user(
        self,
        *,
        actor: AuthenticatedIdentity,
        username: str,
        email: str,
        password: str,
    ) -> User:
        """Create a new active user without assigned roles."""

        if not isinstance(actor, AuthenticatedIdentity):
            raise TypeError(
                "actor must be an AuthenticatedIdentity"
            )

        username_value = Username(username)
        email_value = Email(email)

        if (
            self._user_repository.get_by_username(
                username_value
            )
            is not None
        ):
            raise UsernameAlreadyExists

        if (
            self._user_repository.get_by_email(email_value)
            is not None
        ):
            raise EmailAlreadyExists

        user = User(
            id=UserId.generate(),
            username=username_value,
            email=email_value,
            password_hash=self._password_hasher.hash(
                password
            ),
        )

        self._user_repository.save(user)

        self._audit_repository.record(
            "identity.user.created",
            actor,
            {
                "target_user_id": str(user.id),
                "target_username": user.username.value,
                "target_email": user.email.value,
            },
        )

        return user

    def list_users(
        self,
        *,
        actor: AuthenticatedIdentity,
    ) -> tuple[User, ...]:
        """Return all users ordered by the repository."""

        if not isinstance(actor, AuthenticatedIdentity):
            raise TypeError(
                "actor must be an AuthenticatedIdentity"
            )

        users = self._user_repository.list()

        self._audit_repository.record(
            "identity.users.listed",
            actor,
            {
                "result_count": len(users),
            },
        )

        return users
