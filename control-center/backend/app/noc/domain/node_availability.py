"""Operational availability of a NodeInstance.

ENG-013B — Node SDK
NCS reference: 13-NODE-AVAILABILITY.md
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NodeAvailabilityState(str, Enum):
    """Canonical NodeAvailability states defined by NCS v1.0.0."""

    AVAILABLE = "AVAILABLE"
    LIMITED = "LIMITED"
    DRAINING = "DRAINING"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(cls, value: str) -> "NodeAvailabilityState":
        """Create a canonical availability state from a string."""
        if not isinstance(value, str):
            raise TypeError(
                "NodeAvailabilityState value must be a string"
            )

        normalized = value.strip().upper()

        if not normalized:
            raise ValueError(
                "NodeAvailabilityState value must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported NodeAvailabilityState: {value!r}"
            ) from exc


@dataclass(frozen=True, slots=True)
class NodeAvailability:
    """Current operational availability of a NodeInstance.

    NodeAvailability answers one question:

        Can this NodeInstance accept new work?

    It does not represent health, lifecycle status, capacity,
    utilization or performance.
    """

    state: NodeAvailabilityState

    def __post_init__(self) -> None:
        if not isinstance(self.state, NodeAvailabilityState):
            raise TypeError(
                "NodeAvailability.state must be a "
                "NodeAvailabilityState"
            )

    @classmethod
    def from_value(cls, value: str) -> "NodeAvailability":
        """Create NodeAvailability from a canonical string."""
        return cls(
            state=NodeAvailabilityState.from_value(value)
        )

    @property
    def is_available(self) -> bool:
        return self.state is NodeAvailabilityState.AVAILABLE

    @property
    def is_limited(self) -> bool:
        return self.state is NodeAvailabilityState.LIMITED

    @property
    def is_draining(self) -> bool:
        return self.state is NodeAvailabilityState.DRAINING

    @property
    def is_unavailable(self) -> bool:
        return self.state is NodeAvailabilityState.UNAVAILABLE

    @property
    def is_unknown(self) -> bool:
        return self.state is NodeAvailabilityState.UNKNOWN

    @property
    def accepts_new_work(self) -> bool:
        """Return whether new work may be assigned.

        AVAILABLE and LIMITED accept work.
        DRAINING, UNAVAILABLE and UNKNOWN do not.
        """
        return self.state in {
            NodeAvailabilityState.AVAILABLE,
            NodeAvailabilityState.LIMITED,
        }

    def __str__(self) -> str:
        return self.state.value
