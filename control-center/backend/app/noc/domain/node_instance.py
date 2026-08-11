"""Concrete runtime instance of a NOC Node.

ENG-013B — Node SDK
NCS reference: 09-NODE-INSTANCE.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.noc.domain.node_id import NodeId


@dataclass(frozen=True, slots=True)
class NodeInstanceId:
    """Identity of a concrete Node execution.

    The identifier must be unique within its parent Node.
    It identifies an operational instance and must not be confused
    with the logical NodeId.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()

        if not normalized:
            raise ValueError("NodeInstanceId.value must not be empty")

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(slots=True)
class NodeInstance:
    """Concrete execution of a logical Node.

    A NodeInstance belongs to exactly one Node and owns its dynamic
    operational state.

    Operational components are intentionally optional during initial
    construction because they are populated during the instance
    lifecycle.
    """

    instance_id: NodeInstanceId
    node_id: NodeId
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    info: Any | None = None
    status: Any | None = None
    health: Any | None = None
    availability: Any | None = None
    capabilities: tuple[Any, ...] = ()
    capacity: Any | None = None
    metrics: tuple[Any, ...] = ()
    events: tuple[Any, ...] = ()
    alarms: tuple[Any, ...] = ()
    heartbeat: Any | None = None
    snapshot: Any | None = None

    def __post_init__(self) -> None:
        """Validate NodeInstance invariants."""
        if not isinstance(self.instance_id, NodeInstanceId):
            raise TypeError(
                "NodeInstance.instance_id must be a NodeInstanceId"
            )

        if not isinstance(self.node_id, NodeId):
            raise TypeError(
                "NodeInstance.node_id must be a NodeId"
            )

        if not isinstance(self.created_at, datetime):
            raise TypeError(
                "NodeInstance.created_at must be a datetime"
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "NodeInstance.created_at must be timezone-aware and UTC"
            )

        offset = self.created_at.utcoffset()

        if offset is None or offset.total_seconds() != 0:
            raise ValueError(
                "NodeInstance.created_at must be expressed in UTC"
            )

    @classmethod
    def create(
        cls,
        *,
        instance_id: str,
        node_id: NodeId,
        created_at: datetime | None = None,
    ) -> "NodeInstance":
        """Create a new runtime instance for a logical Node."""
        return cls(
            instance_id=NodeInstanceId(instance_id),
            node_id=node_id,
            created_at=created_at or datetime.now(timezone.utc),
        )

    def belongs_to(self, node_id: NodeId) -> bool:
        """Return whether this instance belongs to the given Node."""
        if not isinstance(node_id, NodeId):
            raise TypeError("node_id must be a NodeId")

        return self.node_id == node_id

    def __str__(self) -> str:
        """Return the canonical operational instance identifier."""
        return str(self.instance_id)
