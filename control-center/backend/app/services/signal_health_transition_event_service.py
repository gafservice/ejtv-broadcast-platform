"""Coordinate SignalHealth transition events with the NOC EventService.

ENG-013C — Signal Health -> NOC integration

This service receives an already-detected SignalHealthTransition,
maps it to an EventRecord through SignalHealthTransitionEventFactory,
and records that event through the existing EventService.

It does not:

- evaluate Signal Health;
- evaluate Media Health;
- evaluate Source Transport Health;
- detect transitions;
- capture MediaMTX state;
- own event persistence;
- create or manage alarms.
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
from app.services.signal_health_transition_detector import (
    SignalHealthTransition,
)
from app.services.signal_health_transition_event_factory import (
    SignalHealthTransitionEventFactory,
)


@dataclass(frozen=True, slots=True)
class SignalHealthTransitionEventResult:
    """Result of processing one optional SignalHealth transition."""

    transition: SignalHealthTransition | None
    event: EventRecord | None
    receipt: EventReceipt | None


class SignalHealthTransitionEventService:
    """Coordinate SignalHealth transitions with EventService."""

    def __init__(
        self,
        *,
        event_service: EventService,
        factory: SignalHealthTransitionEventFactory | None = None,
    ) -> None:
        if not isinstance(event_service, EventService):
            raise TypeError(
                "event_service must be an EventService"
            )

        if (
            factory is not None
            and not isinstance(
                factory,
                SignalHealthTransitionEventFactory,
            )
        ):
            raise TypeError(
                "factory must be a "
                "SignalHealthTransitionEventFactory or None"
            )

        self._event_service = event_service
        self._factory = (
            factory
            if factory is not None
            else SignalHealthTransitionEventFactory()
        )

    @property
    def event_service(self) -> EventService:
        return self._event_service

    @property
    def factory(
        self,
    ) -> SignalHealthTransitionEventFactory:
        return self._factory

    def process_transition(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        transition: SignalHealthTransition | None,
        timestamp: datetime,
    ) -> SignalHealthTransitionEventResult:
        """Record one event when a SignalHealth transition exists."""

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
                SignalHealthTransition,
            )
        ):
            raise TypeError(
                "transition must be a "
                "SignalHealthTransition or None"
            )

        if not isinstance(timestamp, datetime):
            raise TypeError(
                "timestamp must be a datetime"
            )

        if (
            timestamp.tzinfo is None
            or timestamp.utcoffset() is None
        ):
            raise ValueError(
                "timestamp must be timezone-aware"
            )

        if transition is None:
            return SignalHealthTransitionEventResult(
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
            node_id=node_id,
            instance_id=instance_id,
            event=event,
        )

        return SignalHealthTransitionEventResult(
            transition=transition,
            event=event,
            receipt=receipt,
        )
