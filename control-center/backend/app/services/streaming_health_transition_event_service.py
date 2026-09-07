"""Stream Health transition event coordination service.

ENG-013B — Stream Health Contract Block 4

StreamingHealthTransitionEventService receives an already detected
StreamingHealthTransition, converts it into one immutable EventRecord,
and persists it through the existing EventService.

It does not detect Stream Health transitions, evaluate health,
raise alarms, or own event persistence.
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
from app.services.streaming_health_transition_detector import (
    StreamingHealthTransition,
)
from app.services.streaming_health_transition_event_factory import (
    StreamingHealthTransitionEventFactory,
)


@dataclass(frozen=True, slots=True)
class StreamingHealthTransitionEventResult:
    """Result of processing one Stream Health transition."""

    transition: StreamingHealthTransition | None
    event: EventRecord | None
    receipt: EventReceipt | None


class StreamingHealthTransitionEventService:
    """Convert already detected Stream Health transitions into NOC Events."""

    def __init__(
        self,
        *,
        event_service: EventService,
        factory: StreamingHealthTransitionEventFactory | None = None,
    ) -> None:
        if not isinstance(event_service, EventService):
            raise TypeError(
                "event_service must be an EventService"
            )

        if (
            factory is not None
            and not isinstance(
                factory,
                StreamingHealthTransitionEventFactory,
            )
        ):
            raise TypeError(
                "factory must be a "
                "StreamingHealthTransitionEventFactory or None"
            )

        self._event_service = event_service
        self._factory = (
            factory
            if factory is not None
            else StreamingHealthTransitionEventFactory()
        )

    @property
    def event_service(self) -> EventService:
        return self._event_service

    @property
    def factory(
        self,
    ) -> StreamingHealthTransitionEventFactory:
        return self._factory

    def process_transition(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        transition: StreamingHealthTransition | None,
        timestamp: datetime,
    ) -> StreamingHealthTransitionEventResult:
        """Persist one event for one already detected transition."""

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
                StreamingHealthTransition,
            )
        ):
            raise TypeError(
                "transition must be a "
                "StreamingHealthTransition or None"
            )

        if not isinstance(timestamp, datetime):
            raise TypeError(
                "timestamp must be a datetime"
            )

        if transition is None:
            return StreamingHealthTransitionEventResult(
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

        return StreamingHealthTransitionEventResult(
            transition=transition,
            event=event,
            receipt=receipt,
        )
