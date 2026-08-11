"""Operational lifecycle status of a NodeInstance.

ENG-013B — Node SDK
NCS reference: 11-NODE-STATUS.md
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NodeStatusState(str, Enum):
    """Canonical NodeStatus states defined by NCS v1.0.0."""

    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    MAINTENANCE = "MAINTENANCE"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(cls, value: str) -> "NodeStatusState":
        """Create a canonical state from a string value."""
        if not isinstance(value, str):
            raise TypeError("NodeStatusState value must be a string")

        normalized = value.strip().upper()

        if not normalized:
            raise ValueError(
                "NodeStatusState value must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported NodeStatusState: {value!r}"
            ) from exc


@dataclass(frozen=True, slots=True)
class NodeStatus:
    """Current operational lifecycle status of a NodeInstance.

    NodeStatus represents only what the instance is currently doing.
    It does not represent health, availability, performance,
    utilization or capacity.
    """

    state: NodeStatusState

    def __post_init__(self) -> None:
        if not isinstance(self.state, NodeStatusState):
            raise TypeError(
                "NodeStatus.state must be a NodeStatusState"
            )

    @classmethod
    def from_value(cls, value: str) -> "NodeStatus":
        """Create NodeStatus from a canonical string value."""
        return cls(
            state=NodeStatusState.from_value(value)
        )

    @property
    def is_running(self) -> bool:
        """Return whether the instance is executing service work."""
        return self.state in {
            NodeStatusState.RUNNING,
            NodeStatusState.DEGRADED,
        }

    @property
    def is_stopped(self) -> bool:
        """Return whether execution has stopped."""
        return self.state is NodeStatusState.STOPPED

    @property
    def is_failed(self) -> bool:
        """Return whether execution ended because of failure."""
        return self.state is NodeStatusState.FAILED

    @property
    def is_maintenance(self) -> bool:
        """Return whether the instance is under maintenance."""
        return self.state is NodeStatusState.MAINTENANCE

    @property
    def is_unknown(self) -> bool:
        """Return whether the operational state is unknown."""
        return self.state is NodeStatusState.UNKNOWN

    def __str__(self) -> str:
        return self.state.value
