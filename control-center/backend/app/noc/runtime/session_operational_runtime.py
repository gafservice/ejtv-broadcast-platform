"""Operational runtime coordination for multimedia sessions.

ENG-013B — Node SDK

SessionOperationalRuntime coordinates one session-observation cycle.

It detects session lifecycle transitions exactly once, then distributes
those transitions to:

- SessionTransitionEventService for event persistence;
- SessionAlarmRuntime for operational alarm policies.

The runtime does not capture sessions, render dashboards or own alarm
or event persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.sessions import SessionSnapshot
from app.domain.streaming.models import MediaMTXSnapshot
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.session_alarm_runtime import (
    SessionAlarmRuntime,
    SessionAlarmRuntimeResult,
)
from app.noc.services.session_transition_detector import (
    SessionTransition,
    SessionTransitionDetector,
)
from app.noc.services.session_transition_event_service import (
    SessionTransitionEventResult,
    SessionTransitionEventService,
)


@dataclass(frozen=True, slots=True)
class SessionOperationalRuntimeResult:
    """Result of one operational multimedia-session cycle."""

    transitions: tuple[SessionTransition, ...]
    event_result: SessionTransitionEventResult
    alarm_result: SessionAlarmRuntimeResult


class SessionOperationalRuntime:
    """Coordinate session transitions, events and alarms."""

    def __init__(
        self,
        *,
        transition_event_service: SessionTransitionEventService,
        alarm_runtime: SessionAlarmRuntime,
        detector: SessionTransitionDetector | None = None,
    ) -> None:
        if not isinstance(
            transition_event_service,
            SessionTransitionEventService,
        ):
            raise TypeError(
                "transition_event_service must be a "
                "SessionTransitionEventService"
            )

        if not isinstance(
            alarm_runtime,
            SessionAlarmRuntime,
        ):
            raise TypeError(
                "alarm_runtime must be a SessionAlarmRuntime"
            )

        if (
            detector is not None
            and not isinstance(
                detector,
                SessionTransitionDetector,
            )
        ):
            raise TypeError(
                "detector must be a "
                "SessionTransitionDetector or None"
            )

        self._transition_event_service = (
            transition_event_service
        )
        self._alarm_runtime = alarm_runtime
        self._detector = (
            detector
            if detector is not None
            else SessionTransitionDetector()
        )

    @property
    def detector(self) -> SessionTransitionDetector:
        return self._detector

    def process(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        previous: SessionSnapshot | None,
        current: SessionSnapshot,
        media_snapshot: MediaMTXSnapshot,
        timestamp: datetime,
    ) -> SessionOperationalRuntimeResult:
        """Process one session observation cycle."""

        self._validate_inputs(
            node_id=node_id,
            instance_id=instance_id,
            previous=previous,
            current=current,
            media_snapshot=media_snapshot,
            timestamp=timestamp,
        )

        transitions = self._detector.detect(
            previous,
            current,
        )

        event_result = (
            self._transition_event_service.process_transitions(
                node_id=node_id,
                instance_id=instance_id,
                transitions=transitions,
                timestamp=timestamp,
            )
        )

        alarm_result = self._alarm_runtime.process(
            node_id=node_id,
            instance_id=instance_id,
            session_snapshot=current,
            media_snapshot=media_snapshot,
            transitions=transitions,
            timestamp=timestamp,
        )

        return SessionOperationalRuntimeResult(
            transitions=transitions,
            event_result=event_result,
            alarm_result=alarm_result,
        )

    @staticmethod
    def _validate_inputs(
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        previous: SessionSnapshot | None,
        current: SessionSnapshot,
        media_snapshot: MediaMTXSnapshot,
        timestamp: datetime,
    ) -> None:
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
            media_snapshot,
            MediaMTXSnapshot,
        ):
            raise TypeError(
                "media_snapshot must be a MediaMTXSnapshot"
            )

        if not isinstance(timestamp, datetime):
            raise TypeError(
                "timestamp must be a datetime"
            )

        if timestamp.tzinfo is None:
            raise ValueError(
                "timestamp must be timezone-aware and UTC"
            )

        offset = timestamp.utcoffset()

        if (
            offset is None
            or offset != timedelta(0)
        ):
            raise ValueError(
                "timestamp must be expressed in UTC"
            )
