"""Media Health transition event coordination service.

ENG-013C — Media Health -> NOC integration

MediaHealthTransitionEventService receives an already detected
MediaHealthTransition, converts it into one immutable EventRecord,
and persists it through the existing EventService.

It does not detect Media Health transitions, evaluate or stabilize
Media Health, raise alarms, or own event persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.noc.domain.node_event import EventRecord
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.event_service import (
    EventReceipt,
    EventService,
)
from app.services.media_health_transition_detector import (
    MediaHealthTransition,
)
from app.services.media_health_transition_event_factory import (
    MediaHealthTransitionEventFactory,
)


@dataclass(frozen=True, slots=True)
class MediaHealthTransitionEventResult:
    """Result of processing one Media Health transition."""

    transition: MediaHealthTransition | None
    event: EventRecord | None
    receipt: EventReceipt | None


class MediaHealthTransitionEventService:
    """Convert already detected Media Health transitions into NOC Events."""

    def __init__(
        self,
        *,
        event_service: EventService,
        factory: MediaHealthTransitionEventFactory | None = None,
    ) -> None:
        if not isinstance(event_service, EventService):
            raise TypeError(
                "event_service must be an EventService"
            )

        if (
            factory is not None
            and not isinstance(
                factory,
                MediaHealthTransitionEventFactory,
            )
        ):
            raise TypeError(
                "factory must be a "
                "MediaHealthTransitionEventFactory or None"
            )

        self._event_service = event_service
        self._factory = (
            factory
            if factory is not None
            else MediaHealthTransitionEventFactory()
        )

    @property
    def event_service(self) -> EventService:
        return self._event_service

    @property
    def factory(
        self,
    ) -> MediaHealthTransitionEventFactory:
        return self._factory

    def process_transition(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        transition: MediaHealthTransition | None,
        timestamp: datetime,
    ) -> MediaHealthTransitionEventResult:
        """Persist one event for one already detected Media Health transition."""

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
            transition is not None
            and not isinstance(
                transition,
                MediaHealthTransition,
            )
        ):
            raise TypeError(
                "transition must be a "
                "MediaHealthTransition or None"
            )

        if not isinstance(timestamp, datetime):
            raise TypeError(
                "timestamp must be a datetime"
            )

        if transition is None:
            return MediaHealthTransitionEventResult(
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

        return MediaHealthTransitionEventResult(
            transition=transition,
            event=event,
            receipt=receipt,
        )
