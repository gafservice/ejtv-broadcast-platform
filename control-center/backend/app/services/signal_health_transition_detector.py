"""Semantic transition detection for SignalHealth.

ENG-013C — Signal Health -> NOC integration

This module compares consecutive already-evaluated SignalHealth
conclusions and classifies meaningful semantic changes.

It does not:

- evaluate Signal Health;
- evaluate Media Health;
- evaluate Source Transport Health;
- capture MediaMTX state;
- create events;
- create or manage alarms;
- persist state;
- own an observation loop.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.signal_health import SignalHealth
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)


_HEALTH_SEVERITY: dict[HealthStatus, int] = {
    HealthStatus.HEALTHY: 0,
    HealthStatus.DEGRADED: 1,
    HealthStatus.CRITICAL: 2,
}


@dataclass(frozen=True, slots=True)
class SignalHealthTransition:
    """Immutable description of one SignalHealth transition."""

    previous: SignalHealth
    current: SignalHealth
    kind: HealthTransitionKind

    def __post_init__(self) -> None:
        if not isinstance(self.previous, SignalHealth):
            raise TypeError(
                "previous must be a SignalHealth"
            )

        if not isinstance(self.current, SignalHealth):
            raise TypeError(
                "current must be a SignalHealth"
            )

        if not isinstance(
            self.kind,
            HealthTransitionKind,
        ):
            raise TypeError(
                "kind must be a HealthTransitionKind"
            )


class SignalHealthTransitionDetector:
    """Detect meaningful transitions between SignalHealth conclusions."""

    def detect(
        self,
        previous: SignalHealth | None,
        current: SignalHealth,
    ) -> SignalHealthTransition | None:
        """Return one semantic transition or None when status did not change."""

        if previous is not None and not isinstance(
            previous,
            SignalHealth,
        ):
            raise TypeError(
                "previous must be a SignalHealth or None"
            )

        if not isinstance(current, SignalHealth):
            raise TypeError(
                "current must be a SignalHealth"
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
            return SignalHealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.UNKNOWN,
            )

        if current.status is HealthStatus.HEALTHY:
            return SignalHealthTransition(
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
            return SignalHealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.DEGRADED,
            )

        if current_severity < previous_severity:
            return SignalHealthTransition(
                previous=previous,
                current=current,
                kind=HealthTransitionKind.IMPROVED,
            )

        return None

    @staticmethod
    def _validate_identity(
        previous: SignalHealth,
        current: SignalHealth,
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
                "SignalHealth identity must remain unchanged "
                "across a transition"
            )
