"""Operational health evaluation of a NodeInstance.

ENG-013B — Node SDK
NCS reference: 12-NODE-HEALTH.md
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NodeHealthState(str, Enum):
    """Canonical NodeHealth states defined by NCS v1.0.0."""

    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(cls, value: str) -> "NodeHealthState":
        """Create a canonical health state from a string value."""
        if not isinstance(value, str):
            raise TypeError("NodeHealthState value must be a string")

        normalized = value.strip().upper()

        if not normalized:
            raise ValueError(
                "NodeHealthState value must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported NodeHealthState: {value!r}"
            ) from exc


_HEALTH_SEVERITY: dict[NodeHealthState, int] = {
    NodeHealthState.HEALTHY: 0,
    NodeHealthState.WARNING: 1,
    NodeHealthState.DEGRADED: 2,
    NodeHealthState.CRITICAL: 3,
}


@dataclass(frozen=True, slots=True)
class NodeHealth:
    """Current operational health of a NodeInstance.

    NodeHealth represents only the integral health evaluation of the
    instance. It does not represent status, availability, capacity,
    metrics or historical diagnostic information.
    """

    state: NodeHealthState

    def __post_init__(self) -> None:
        if not isinstance(self.state, NodeHealthState):
            raise TypeError(
                "NodeHealth.state must be a NodeHealthState"
            )

    @classmethod
    def from_value(cls, value: str) -> "NodeHealth":
        """Create NodeHealth from a canonical string value."""
        return cls(
            state=NodeHealthState.from_value(value)
        )

    @property
    def is_healthy(self) -> bool:
        return self.state is NodeHealthState.HEALTHY

    @property
    def is_warning(self) -> bool:
        return self.state is NodeHealthState.WARNING

    @property
    def is_degraded(self) -> bool:
        return self.state is NodeHealthState.DEGRADED

    @property
    def is_critical(self) -> bool:
        return self.state is NodeHealthState.CRITICAL

    @property
    def is_unknown(self) -> bool:
        return self.state is NodeHealthState.UNKNOWN

    @property
    def severity(self) -> int | None:
        """Return the ordered severity or None for UNKNOWN."""
        return _HEALTH_SEVERITY.get(self.state)

    def worse_than(self, other: "NodeHealth") -> bool:
        """Return whether this health is worse than another known state.

        UNKNOWN is intentionally not ordered and therefore cannot be
        considered better or worse than a known health state.
        """
        if not isinstance(other, NodeHealth):
            raise TypeError("other must be a NodeHealth")

        if self.severity is None or other.severity is None:
            return False

        return self.severity > other.severity

    def better_than(self, other: "NodeHealth") -> bool:
        """Return whether this health is better than another known state.

        UNKNOWN is intentionally not ordered.
        """
        if not isinstance(other, NodeHealth):
            raise TypeError("other must be a NodeHealth")

        if self.severity is None or other.severity is None:
            return False

        return self.severity < other.severity

    def __str__(self) -> str:
        return self.state.value
