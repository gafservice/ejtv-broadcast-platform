"""Semantic transition detection for stabilized MediaHealth.

ENG-013C — Media Health -> NOC integration

This module compares consecutive stabilized MediaHealth values and
classifies meaningful semantic changes.

It does not:

- evaluate Media Health;
- stabilize Media Health;
- create events;
- create or manage alarms;
- persist state.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import MediaHealth
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)


_HEALTH_SEVERITY: dict[HealthStatus, int] = {
    HealthStatus.HEALTHY: 0,
    HealthStatus.DEGRADED: 1,
    HealthStatus.CRITICAL: 2,
}


@dataclass(frozen=True, slots=True)
class MediaHealthTransition:
    """Immutable description of one MediaHealth transition."""

    previous: MediaHealth
    current: MediaHealth
    kind: HealthTransitionKind

    def __post_init__(self) -> None:
        if not isinstance(self.previous, MediaHealth):
            raise TypeError(
                "previous must be a MediaHealth"
            )

        if not isinstance(self.current, MediaHealth):
            raise TypeError(
                "current must be a MediaHealth"
            )

        if not isinstance(
            self.kind,
            HealthTransitionKind,
        ):
            raise TypeError(
                "kind must be a HealthTransitionKind"
            )


class MediaHealthTransitionDetector:
    """Detect meaningful transitions between stabilized MediaHealth values."""

    def detect(
        self,
        previous: MediaHealth | None,
        current: MediaHealth,
    ) -> MediaHealthTransition | None:
        """Return one semantic transition or None when status did not change."""

        if previous is not None and not isinstance(
            previous,
            MediaHealth,
        ):
            raise TypeError(
                "previous must be a MediaHealth or None"
            )

        if not isinstance(current, MediaHealth):
            raise TypeError(
                "current must be a MediaHealth"
            )

        if previous is None:
            return None

        self._validate_identity(
            previous,
            current,
        )

        if previous.status is current.status:
            return None

        if (
            previous.status is HealthStatus.UNKNOWN
            or current.status is HealthStatus.UNKNOWN
        ):
            return MediaHealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.UNKNOWN,
            )

        if current.status is HealthStatus.HEALTHY:
            return MediaHealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.RECOVERED,
            )

        previous_severity = _HEALTH_SEVERITY[
            previous.status
        ]
        current_severity = _HEALTH_SEVERITY[
            current.status
        ]

        if current_severity > previous_severity:
            return MediaHealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.DEGRADED,
            )

        if current_severity < previous_severity:
            return MediaHealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.IMPROVED,
            )

        return None

    @staticmethod
    def _validate_identity(
        previous: MediaHealth,
        current: MediaHealth,
    ) -> None:
        previous_identity = (
            previous.profile_id,
            previous.service_id,
            previous.path_name,
        )
        current_identity = (
            current.profile_id,
            current.service_id,
            current.path_name,
        )

        if previous_identity != current_identity:
            raise ValueError(
                "MediaHealth identity must remain unchanged "
                "across a transition"
            )
