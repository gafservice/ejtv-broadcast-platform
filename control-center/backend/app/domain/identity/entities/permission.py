from dataclasses import dataclass

from app.domain.identity.value_objects import PermissionName


@dataclass(frozen=True, slots=True)
class Permission:
    """
    Represents a business permission within the IAM domain.

    The permission name is its natural identity.
    """

    name: PermissionName

    def __str__(self) -> str:
        return str(self.name)
