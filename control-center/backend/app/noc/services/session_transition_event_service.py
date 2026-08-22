"""Session transition event coordination service for the NOC.

ENG-013B — Node SDK

SessionTransitionEventService coordinates detection of multimedia session
lifecycle changes, converts them into immutable EventRecord objects and
persists them through EventService.

It does not capture sessions, modify session state, render the dashboard or
raise alarms.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.sessions import SessionSnapshot
from app.noc.domain.node_event import EventRecord
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.event_service import (
    EventReceipt,
    EventService,
)
from app.noc.services.session_transition_detector import (
    SessionTransition,
    SessionTransitionDetector,
)
from app.noc.services.session_transition_event_factory import (
    SessionTransitionEventFactory,
)


@dataclass(frozen=True, slots=True)
class SessionTransitionEventResult:
    """Result of one session-transition event processing operation."""

    transitions: tuple[SessionTransition, ...]
    events: tuple[EventRecord, ...]
    receipts: tuple[EventReceipt, ...]


class SessionTransitionEventService:
    """Coordinate session transition detection and event persistence."""

    def __init__(
        self,
        *,
        event_service: EventService,
        detector: SessionTransitionDetector | None = None,
        factory: SessionTransitionEventFactory | None = None,
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
                SessionTransitionDetector,
            )
        ):
            raise TypeError(
                "detector must be a SessionTransitionDetector or None"
            )

        if (
            factory is not None
            and not isinstance(
                factory,
                SessionTransitionEventFactory,
            )
        ):
            raise TypeError(
                "factory must be a SessionTransitionEventFactory or None"
            )

        self._event_service = event_service
        self._detector = (
            detector
            or SessionTransitionDetector()
        )
        self._factory = (
            factory
            or SessionTransitionEventFactory()
        )

    @property
    def event_service(self) -> EventService:
        return self._event_service

    @property
    def detector(self) -> SessionTransitionDetector:
        return self._detector

    @property
    def factory(self) -> SessionTransitionEventFactory:
        return self._factory

    def process(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        previous: SessionSnapshot | None,
        current: SessionSnapshot,
        timestamp: datetime,
    ) -> SessionTransitionEventResult:
        """Detect session lifecycle changes and persist their events."""

        if not isinstance(
            node_id,
            NodeId,
        ):
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
                SessionSnapshot,
            )
        ):
            raise TypeError(
                "previous must be a SessionSnapshot or None"
            )

        if not isinstance(
            current,
            SessionSnapshot,
        ):
            raise TypeError(
                "current must be a SessionSnapshot"
            )

        if not isinstance(
            timestamp,
            datetime,
        ):
            raise TypeError(
                "timestamp must be a datetime"
            )

        transitions = self._detector.detect(
            previous,
            current,
        )

        events: list[EventRecord] = []
        receipts: list[EventReceipt] = []

        for transition in transitions:
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

            events.append(event)
            receipts.append(receipt)

        return SessionTransitionEventResult(
            transitions=transitions,
            events=tuple(events),
            receipts=tuple(receipts),
        )
