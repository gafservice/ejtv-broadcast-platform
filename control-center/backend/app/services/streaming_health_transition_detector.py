"""Semantic transition detection for stabilized StreamingHealth.

ENG-013B — Stream Health Contract Block 3

This module compares consecutive effective StreamingHealth observations
and classifies meaningful semantic changes.

It does not evaluate health, stabilize health, persist events or raise
alarms.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.streaming.health import (
    HealthStatus,
    StreamingHealth,
)
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)


_HEALTH_SEVERITY: dict[HealthStatus, int] = {
    HealthStatus.HEALTHY: 0,
    HealthStatus.DEGRADED: 1,
    HealthStatus.CRITICAL: 2,
}


@dataclass(frozen=True, slots=True)
class StreamingHealthTransition:
    """Immutable description of one StreamingHealth transition."""

    previous: StreamingHealth
    current: StreamingHealth
    kind: HealthTransitionKind

    def __post_init__(self) -> None:
        if not isinstance(self.previous, StreamingHealth):
            raise TypeError(
                "previous must be a StreamingHealth"
            )

        if not isinstance(self.current, StreamingHealth):
            raise TypeError(
                "current must be a StreamingHealth"
            )

        if not isinstance(
            self.kind,
            HealthTransitionKind,
        ):
            raise TypeError(
                "kind must be a HealthTransitionKind"
            )


class StreamingHealthTransitionDetector:
    """Detect meaningful transitions between StreamingHealth values."""

    def detect(
        self,
        previous: StreamingHealth | None,
        current: StreamingHealth,
    ) -> StreamingHealthTransition | None:
        """Return one semantic transition or None when status did not change."""

        if previous is not None and not isinstance(
            previous,
            StreamingHealth,
        ):
            raise TypeError(
                "previous must be a StreamingHealth or None"
            )

        if not isinstance(current, StreamingHealth):
            raise TypeError(
                "current must be a StreamingHealth"
            )

        if previous is None:
            return None

        if previous.status is current.status:
            return None

        if (
            previous.status is HealthStatus.UNKNOWN
            or current.status is HealthStatus.UNKNOWN
        ):
            return StreamingHealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.UNKNOWN,
            )

        if current.status is HealthStatus.HEALTHY:
            return StreamingHealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.RECOVERED,
            )

        previous_severity = _HEALTH_SEVERITY[previous.status]
        current_severity = _HEALTH_SEVERITY[current.status]

        if current_severity > previous_severity:
            return StreamingHealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.DEGRADED,
            )

        if current_severity < previous_severity:
            return StreamingHealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.IMPROVED,
            )

        return None
