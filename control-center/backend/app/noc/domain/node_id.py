"""Canonical logical identity for a NOC Node.

ENG-013B — Node SDK
NCS reference: 07-NODE-ID.md
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class NodeId:
    """Stable logical identity of a Node.

    A NodeId belongs to the logical Node, not to a NodeInstance.
    It must remain stable for the complete logical lifetime of the Node.

    The identifier is intentionally format-agnostic. UUID, ULID and
    organization-defined identifiers are valid as long as uniqueness is
    guaranteed by the platform.
    """

    id: str
    name: str
    display_name: str
    created_at: datetime

    def __post_init__(self) -> None:
        """Validate the invariants defined by the Node Contract."""
        object.__setattr__(self, "id", self.id.strip())
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "display_name", self.display_name.strip())

        if not self.id:
            raise ValueError("NodeId.id must not be empty")

        if not self.name:
            raise ValueError("NodeId.name must not be empty")

        if not self.display_name:
            raise ValueError("NodeId.display_name must not be empty")

        if not isinstance(self.created_at, datetime):
            raise TypeError("NodeId.created_at must be a datetime")

        if self.created_at.tzinfo is None:
            raise ValueError(
                "NodeId.created_at must be timezone-aware and expressed in UTC"
            )

        offset = self.created_at.utcoffset()
        if offset is None or offset.total_seconds() != 0:
            raise ValueError(
                "NodeId.created_at must be expressed in UTC"
            )

    @classmethod
    def create(
        cls,
        *,
        id: str,
        name: str,
        display_name: str,
        created_at: datetime | None = None,
    ) -> "NodeId":
        """Create a NodeId using the current UTC time when omitted."""
        return cls(
            id=id,
            name=name,
            display_name=display_name,
            created_at=created_at or datetime.now(timezone.utc),
        )

    def __str__(self) -> str:
        """Return the canonical identifier."""
        return self.id
