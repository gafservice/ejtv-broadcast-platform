"""Health transition event coordination service for the NOC.

ENG-013B — Node SDK

HealthTransitionEventService coordinates the conversion of NodeHealth
changes into persisted operational EventRecord objects.

It detects transitions, maps them to events and delegates persistence
to EventService.

It does not evaluate health, publish NodeHealth or raise alarms.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.noc.domain.node_event import EventRecord
from app.noc.domain.node_health import NodeHealth
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.event_service import (
    EventReceipt,
    EventService,
)
from app.noc.services.health_transition_detector import (
    HealthTransition,
    HealthTransitionDetector,
)
from app.noc.services.health_transition_event_factory import (
    HealthTransitionEventFactory,
)


@dataclass(frozen=True, slots=True)
class HealthTransitionEventResult:
    """Result of one health-transition event processing operation."""

    transition: HealthTransition | None
    event: EventRecord | None
    receipt: EventReceipt | None


class HealthTransitionEventService:
    """Coordinate NodeHealth transition detection and event persistence."""

    def __init__(
        self,
        *,
        event_service: EventService,
        detector: HealthTransitionDetector | None = None,
        factory: HealthTransitionEventFactory | None = None,
    ) -> None:
        if not isinstance(
            event_service,
            EventService,
        ):
            raise TypeError(
                "event_service must be an EventService"
            )

        if (
            detector is not None
            and not isinstance(
                detector,
                HealthTransitionDetector,
            )
        ):
            raise TypeError(
                "detector must be a HealthTransitionDetector or None"
            )

        if (
            factory is not None
            and not isinstance(
                factory,
                HealthTransitionEventFactory,
            )
        ):
            raise TypeError(
                "factory must be a HealthTransitionEventFactory or None"
            )

        self._event_service = event_service
        self._detector = (
            detector
            or HealthTransitionDetector()
        )
        self._factory = (
            factory
            or HealthTransitionEventFactory()
        )

    @property
    def event_service(self) -> EventService:
        return self._event_service

    @property
    def detector(self) -> HealthTransitionDetector:
        return self._detector

    @property
    def factory(self) -> HealthTransitionEventFactory:
        return self._factory

    def process(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        previous: NodeHealth | None,
        current: NodeHealth,
        timestamp: datetime,
    ) -> HealthTransitionEventResult:
        """Detect a health transition and persist its event when present."""

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

        if (
            previous is not None
            and not isinstance(
                previous,
                NodeHealth,
            )
        ):
            raise TypeError(
                "previous must be a NodeHealth or None"
            )

        if not isinstance(current, NodeHealth):
            raise TypeError(
                "current must be a NodeHealth"
            )

        if not isinstance(timestamp, datetime):
            raise TypeError(
                "timestamp must be a datetime"
            )

        transition = self._detector.detect(
            previous,
            current,
        )

        if transition is None:
            return HealthTransitionEventResult(
                transition=None,
                event=None,
                receipt=None,
            )

        event = self._factory.create(
            transition=transition,
            source=instance_id,
            timestamp=timestamp,
        )

        receipt = self._event_service.record(
            node_id,
            instance_id,
            event,
        )

        return HealthTransitionEventResult(
            transition=transition,
            event=event,
            receipt=receipt,
        )

