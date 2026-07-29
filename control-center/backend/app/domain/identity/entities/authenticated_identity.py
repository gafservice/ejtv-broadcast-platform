from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.domain.identity.value_objects import (
    PermissionName,
    RoleName,
    UserId,
    Username,
)

if TYPE_CHECKING:
    from app.domain.identity.entities.user import User


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    """
    Represents an identity whose credentials were already validated.

    This entity contains only the information required to identify and
    authorize an authenticated principal. It remains independent from
    tokens, HTTP, persistence, sessions, and authentication frameworks.
    """

    user_id: UserId
    username: Username
    roles: frozenset[RoleName] = field(default_factory=frozenset)
    permissions: frozenset[PermissionName] = field(
        default_factory=frozenset
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "roles", frozenset(self.roles))
        object.__setattr__(
            self,
            "permissions",
            frozenset(self.permissions),
        )

    @classmethod
    def from_user(cls, user: User) -> AuthenticatedIdentity:
        """
        Build an authenticated identity from a validated active user.

        Credential and user-status validation belongs to the authentication
        use case. This factory only projects the user's effective identity
        and authorization information.
        """

        role_names = frozenset(role.name for role in user.roles)

        permission_names = frozenset(
            permission.name
            for role in user.roles
            for permission in role.permissions
        )

        return cls(
            user_id=user.id,
            username=user.username,
            roles=role_names,
            permissions=permission_names,
        )

    def has_role(self, role_name: RoleName) -> bool:
        """Return whether the identity owns the named role."""

        return role_name in self.roles

    def has_permission(
        self,
        permission_name: PermissionName,
    ) -> bool:
        """Return whether the identity owns the named permission."""

        return permission_name in self.permissions
