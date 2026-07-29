from dataclasses import dataclass, field

from app.domain.identity.entities.permission import Permission
from app.domain.identity.value_objects import PermissionName, RoleName


@dataclass(frozen=True, slots=True)
class Role:
    """
    Represents a role within the IAM domain.

    A role groups a unique, immutable collection of permissions.
    The role name is its natural identity.
    """

    name: RoleName
    permissions: frozenset[Permission] = field(
        default_factory=frozenset
    )

    def has_permission(
        self,
        permission: Permission,
    ) -> bool:
        """Return whether the role contains the given permission."""
        return permission in self.permissions

    def has_permission_name(
        self,
        permission_name: PermissionName,
    ) -> bool:
        """Return whether the role contains a permission with the given name."""
        return any(
            permission.name == permission_name
            for permission in self.permissions
        )

    def __str__(self) -> str:
        return str(self.name)
