"""Node health transition detection for the NOC.

ENG-013B — Node SDK

HealthTransitionDetector compares the previously published NodeHealth
against the newly evaluated NodeHealth.

It does not publish health, persist events or raise alarms.
Its only responsibility is to classify meaningful health transitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)


class HealthTransitionKind(str, Enum):
    """Classification of a NodeHealth state transition."""

    DEGRADED = "DEGRADED"
    IMPROVED = "IMPROVED"
    RECOVERED = "RECOVERED"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class HealthTransition:
    """Immutable description of one NodeHealth transition."""

    previous: NodeHealth
    current: NodeHealth
    kind: HealthTransitionKind

    def __post_init__(self) -> None:
        if not isinstance(self.previous, NodeHealth):
            raise TypeError(
                "previous must be a NodeHealth"
            )

        if not isinstance(self.current, NodeHealth):
            raise TypeError(
                "current must be a NodeHealth"
            )

        if not isinstance(
            self.kind,
            HealthTransitionKind,
        ):
            raise TypeError(
                "kind must be a HealthTransitionKind"
            )


class HealthTransitionDetector:
    """Detect meaningful transitions between NodeHealth values."""

    def detect(
        self,
        previous: NodeHealth | None,
        current: NodeHealth,
    ) -> HealthTransition | None:
        """Return a classified transition or None when nothing changed."""

        if previous is not None and not isinstance(
            previous,
            NodeHealth,
        ):
            raise TypeError(
                "previous must be a NodeHealth or None"
            )

        if not isinstance(current, NodeHealth):
            raise TypeError(
                "current must be a NodeHealth"
            )

        if previous is None:
            return None

        if previous.state is current.state:
            return None

        if (
            previous.state is NodeHealthState.UNKNOWN
            or current.state is NodeHealthState.UNKNOWN
        ):
            return HealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.UNKNOWN,
            )

        if current.state is NodeHealthState.HEALTHY:
            return HealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.RECOVERED,
            )

        if current.worse_than(previous):
            return HealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.DEGRADED,
            )

        if current.better_than(previous):
            return HealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.IMPROVED,
            )

        return None
