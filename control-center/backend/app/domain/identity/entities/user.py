from dataclasses import dataclass, field, replace

from app.domain.identity.entities.permission import Permission
from app.domain.identity.entities.role import Role
from app.domain.identity.enums import UserStatus
from app.domain.identity.value_objects import (
    Email,
    PasswordHash,
    PermissionName,
    RoleName,
    UserId,
    Username,
)


@dataclass(frozen=True, slots=True)
class User:
    """
    Represents a user within the IAM domain.

    The entity contains domain behavior only and remains independent
    from persistence, cryptography, tokens, HTTP, and web frameworks.
    """

    id: UserId
    username: Username
    email: Email
    password_hash: PasswordHash
    roles: frozenset[Role] = field(default_factory=frozenset)
    status: UserStatus = UserStatus.ACTIVE

    def __post_init__(self) -> None:
        object.__setattr__(self, "roles", frozenset(self.roles))

    def is_active(self) -> bool:
        """Return whether the user is active."""

        return self.status is UserStatus.ACTIVE

    def is_locked(self) -> bool:
        """Return whether the user is locked."""

        return self.status is UserStatus.LOCKED

    def with_status(
        self,
        status: UserStatus,
    ) -> "User":
        """Return a copy of the user with a new status."""

        if not isinstance(status, UserStatus):
            raise TypeError("status must be a UserStatus")

        return replace(
            self,
            status=status,
        )

    def with_password_hash(
        self,
        password_hash: PasswordHash,
    ) -> "User":
        """Return a copy of the user with a new password hash."""

        if not isinstance(password_hash, PasswordHash):
            raise TypeError(
                "password_hash must be a PasswordHash"
            )

        return replace(
            self,
            password_hash=password_hash,
        )

    def has_role(self, role: Role) -> bool:
        """Return whether the user owns the given role."""

        return role in self.roles

    def has_role_name(self, role_name: RoleName) -> bool:
        """Return whether the user owns a role with the given name."""

        return any(role.name == role_name for role in self.roles)

    def has_permission(self, permission: Permission) -> bool:
        """Return whether an assigned role contains the permission."""

        return any(
            role.has_permission(permission)
            for role in self.roles
        )

    def has_permission_name(
        self,
        permission_name: PermissionName,
    ) -> bool:
        """Return whether an assigned role contains the named permission."""

        return any(
            role.has_permission_name(permission_name)
            for role in self.roles
        )
