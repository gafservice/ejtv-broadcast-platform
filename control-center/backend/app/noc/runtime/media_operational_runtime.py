"""Operational coordination for stabilized Media Health.

ENG-013C — Media Health -> NOC integration

MediaOperationalRuntime receives consecutive stabilized MediaHealth
values, preserves the previous value independently per Media identity,
detects semantic transitions, and forwards real transitions to the
Media Health transition event service.

It does not:

- observe physical media;
- evaluate Media Health;
- stabilize Media Health;
- define alarm policy;
- own event persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.streaming.media_health import MediaHealth
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.services.media_health_transition_detector import (
    MediaHealthTransition,
    MediaHealthTransitionDetector,
)


MediaHealthIdentity = tuple[
    str,
    str,
    str | None,
]


@dataclass(frozen=True, slots=True)
class MediaOperationalRuntimeResult:
    """Result of processing one stabilized MediaHealth value."""

    transition: MediaHealthTransition | None
    event_result: Any | None


class MediaOperationalRuntime:
    """Coordinate stabilized Media Health with operational NOC events."""

    def __init__(
        self,
        *,
        transition_detector: MediaHealthTransitionDetector,
        transition_event_service: Any,
    ) -> None:
        if not isinstance(
            transition_detector,
            MediaHealthTransitionDetector,
        ):
            raise TypeError(
                "transition_detector must be a "
                "MediaHealthTransitionDetector"
            )

        if transition_event_service is None:
            raise TypeError(
                "transition_event_service must not be None"
            )

        process_transition = getattr(
            transition_event_service,
            "process_transition",
            None,
        )

        if not callable(process_transition):
            raise TypeError(
                "transition_event_service must provide "
                "process_transition"
            )

        self._transition_detector = (
            transition_detector
        )
        self._transition_event_service = (
            transition_event_service
        )

        self._previous_health_by_identity: dict[
            MediaHealthIdentity,
            MediaHealth,
        ] = {}

    @property
    def transition_detector(
        self,
    ) -> MediaHealthTransitionDetector:
        return self._transition_detector

    @property
    def transition_event_service(
        self,
    ) -> Any:
        return self._transition_event_service

    def process_health(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        health: MediaHealth,
        observed_at: datetime,
    ) -> MediaOperationalRuntimeResult:
        """Process one stabilized Media Health observation."""

        if not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId"
            )

        if not isinstance(
            instance_id,
            NodeInstanceId,
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

        if not isinstance(health, MediaHealth):
            raise TypeError(
                "health must be a MediaHealth"
            )

        if not isinstance(observed_at, datetime):
            raise TypeError(
                "observed_at must be a datetime"
            )

        identity = self._identity(health)

        previous = (
            self._previous_health_by_identity.get(
                identity
            )
        )

        transition = (
            self._transition_detector.detect(
                previous,
                health,
            )
        )

        if transition is None:
            self._previous_health_by_identity[
                identity
            ] = health

            return MediaOperationalRuntimeResult(
                transition=None,
                event_result=None,
            )

        event_result = (
            self._transition_event_service.process_transition(
                node_id=node_id,
                instance_id=instance_id,
                transition=transition,
                timestamp=observed_at,
            )
        )

        # A transition becomes the new baseline only after its
        # operational event has been accepted successfully.
        self._previous_health_by_identity[
            identity
        ] = health

        return MediaOperationalRuntimeResult(
            transition=transition,
            event_result=event_result,
        )

    @staticmethod
    def _identity(
        health: MediaHealth,
    ) -> MediaHealthIdentity:
        return (
            health.profile_id,
            health.service_id,
            health.path_name,
        )
