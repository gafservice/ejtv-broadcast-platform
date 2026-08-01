"""Domain contract for canonical Identity catalog persistence."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.identity.entities import Role
from app.domain.identity.value_objects import RoleName


@runtime_checkable
class IdentityCatalogRepository(Protocol):
    """Persistence contract for canonical roles and permissions."""

    def get_role(
        self,
        role_name: RoleName,
    ) -> Role | None:
        """Return the role identified by ``role_name``."""
        ...

    def list_roles(self) -> tuple[Role, ...]:
        """Return all persisted roles ordered by name."""
        ...

    def save_role(self, role: Role) -> None:
        """Create or synchronize a role and its permissions."""
        ...
