"""Application service for Identity user administration."""

from __future__ import annotations

from app.domain.identity.catalog import (
    ADMINISTRATOR_ROLE,
    DEFAULT_ROLES,
    RoleDefinition,
    get_role_definition,
)
from app.domain.identity.entities import (
    AuthenticatedIdentity,
    Permission,
    Role,
    User,
)
from app.domain.identity.exceptions import (
    CannotRemoveLastAdministrator,
    EmailAlreadyExists,
    RoleNotFound,
    UserNotFound,
    UsernameAlreadyExists,
)
from app.domain.identity.protocols import (
    AuditRepository,
    PasswordHasher,
    UserRepository,
)
from app.domain.identity.enums import UserStatus
from app.domain.identity.value_objects import (
    Email,
    RoleName,
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

    def get_user(
        self,
        *,
        actor: AuthenticatedIdentity,
        user_id: str,
    ) -> User:
        """Return a user by identifier."""

        self._validate_actor(actor)

        user = self._get_required_user(user_id)

        self._audit_repository.record(
            "identity.user.retrieved",
            actor,
            {
                "target_user_id": str(user.id),
                "target_username": user.username.value,
            },
        )

        return user

    def change_user_status(
        self,
        *,
        actor: AuthenticatedIdentity,
        user_id: str,
        status: UserStatus,
    ) -> User:
        """Change the operational status of a user."""

        self._validate_actor(actor)

        if not isinstance(status, UserStatus):
            raise TypeError("status must be a UserStatus")

        user = self._get_required_user(user_id)
        updated_user = user.with_status(status)

        self._user_repository.save(updated_user)

        self._audit_repository.record(
            "identity.user.status_changed",
            actor,
            {
                "target_user_id": str(updated_user.id),
                "target_username": updated_user.username.value,
                "previous_status": user.status.value,
                "new_status": updated_user.status.value,
            },
        )

        return updated_user

    def change_password(
        self,
        *,
        actor: AuthenticatedIdentity,
        user_id: str,
        password: str,
    ) -> User:
        """Replace a user's password hash."""

        self._validate_actor(actor)

        user = self._get_required_user(user_id)

        updated_user = user.with_password_hash(
            self._password_hasher.hash(password)
        )

        self._user_repository.save(updated_user)

        self._audit_repository.record(
            "identity.user.password_changed",
            actor,
            {
                "target_user_id": str(updated_user.id),
                "target_username": updated_user.username.value,
            },
        )

        return updated_user

    def list_roles(
        self,
        *,
        actor: AuthenticatedIdentity,
    ) -> tuple[Role, ...]:
        """Return all canonical roles ordered by name."""

        self._validate_actor(actor)

        roles = tuple(
            self._build_role(definition)
            for definition in sorted(
                DEFAULT_ROLES,
                key=lambda item: item.name.value,
            )
        )

        self._audit_repository.record(
            "identity.roles.listed",
            actor,
            {
                "result_count": len(roles),
            },
        )

        return roles

    def assign_role(
        self,
        *,
        actor: AuthenticatedIdentity,
        user_id: str,
        role_name: str,
    ) -> User:
        """Assign a canonical role to a user."""

        self._validate_actor(actor)

        user = self._get_required_user(user_id)
        role = self._get_required_role(role_name)

        if user.has_role_name(role.name):
            updated_user = user
            changed = False
        else:
            updated_user = user.with_role(role)
            self._user_repository.save(updated_user)
            changed = True

        self._audit_repository.record(
            "identity.user.role_assigned",
            actor,
            {
                "target_user_id": str(user.id),
                "target_username": user.username.value,
                "role": role.name.value,
                "changed": changed,
            },
        )

        return updated_user

    def remove_role(
        self,
        *,
        actor: AuthenticatedIdentity,
        user_id: str,
        role_name: str,
    ) -> User:
        """Remove a canonical role from a user."""

        self._validate_actor(actor)

        user = self._get_required_user(user_id)
        role = self._get_required_role(role_name)

        if not user.has_role_name(role.name):
            updated_user = user
            changed = False
        else:
            if role.name == ADMINISTRATOR_ROLE.name:
                self._ensure_other_administrator_exists(
                    user.id
                )

            updated_user = user.without_role(role.name)
            self._user_repository.save(updated_user)
            changed = True

        self._audit_repository.record(
            "identity.user.role_removed",
            actor,
            {
                "target_user_id": str(user.id),
                "target_username": user.username.value,
                "role": role.name.value,
                "changed": changed,
            },
        )

        return updated_user

    def list_users(
        self,
        *,
        actor: AuthenticatedIdentity,
    ) -> tuple[User, ...]:
        """Return all users ordered by the repository."""

        self._validate_actor(actor)

        users = self._user_repository.list()

        self._audit_repository.record(
            "identity.users.listed",
            actor,
            {
                "result_count": len(users),
            },
        )

        return users

    @staticmethod
    def _validate_actor(
        actor: AuthenticatedIdentity,
    ) -> None:
        """Validate administrative actor."""

        if not isinstance(actor, AuthenticatedIdentity):
            raise TypeError(
                "actor must be an AuthenticatedIdentity"
            )

    def _get_required_user(
        self,
        user_id: str,
    ) -> User:
        """Return an existing user or raise."""

        user = self._user_repository.get_by_id(
            UserId.from_string(user_id)
        )

        if user is None:
            raise UserNotFound

        return user

    @staticmethod
    def _build_role(
        definition: RoleDefinition,
    ) -> Role:
        """Build a domain Role from the canonical catalog."""

        if not isinstance(definition, RoleDefinition):
            raise TypeError(
                "definition must be a RoleDefinition"
            )

        return Role(
            name=definition.name,
            permissions=frozenset(
                Permission(name=permission_name)
                for permission_name in definition.permissions
            ),
        )

    def _get_required_role(
        self,
        role_name: str,
    ) -> Role:
        """Return a canonical role or raise."""

        definition = get_role_definition(
            RoleName(role_name)
        )

        if definition is None:
            raise RoleNotFound

        return self._build_role(definition)

    def _ensure_other_administrator_exists(
        self,
        excluded_user_id: UserId,
    ) -> None:
        """Prevent removal of the last administrator."""

        has_other_administrator = any(
            user.id != excluded_user_id
            and user.has_role_name(
                ADMINISTRATOR_ROLE.name
            )
            for user in self._user_repository.list()
        )

        if not has_other_administrator:
            raise CannotRemoveLastAdministrator

