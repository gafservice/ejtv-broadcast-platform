"""Health transition to operational event mapping for the NOC.

ENG-013B — Node SDK

HealthTransitionEventFactory converts a classified NodeHealth transition
into an immutable EventRecord.

It does not persist events, evaluate health or raise alarms.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_health import NodeHealthState
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.health_transition_detector import (
    HealthTransition,
    HealthTransitionKind,
)


class HealthTransitionEventFactory:
    """Create EventRecord objects from NodeHealth transitions."""

    def create(
        self,
        *,
        transition: HealthTransition,
        source: NodeInstanceId,
        timestamp: datetime,
    ) -> EventRecord:
        """Create one immutable operational event."""

        if not isinstance(
            transition,
            HealthTransition,
        ):
            raise TypeError(
                "transition must be a HealthTransition"
            )

        if not isinstance(
            source,
            NodeInstanceId,
        ):
            raise TypeError(
                "source must be a NodeInstanceId"
            )

        self._validate_timestamp(
            timestamp
        )

        event_type = self._event_type(
            transition
        )

        severity = self._severity(
            transition
        )

        previous = transition.previous.state.value
        current = transition.current.state.value
        kind = transition.kind.value

        return EventRecord(
            event_id=self._event_id(),
            event_type=event_type,
            severity=severity,
            timestamp=timestamp,
            source=source,
            title=self._title(
                transition
            ),
            description=self._description(
                transition
            ),
            attributes={
                "previous": previous,
                "current": current,
                "transition": kind,
            },
        )

    @staticmethod
    def _event_id() -> str:
        return f"evt-{uuid4().hex}"

    @staticmethod
    def _event_type(
        transition: HealthTransition,
    ) -> str:
        if (
            transition.kind
            is HealthTransitionKind.DEGRADED
        ):
            return "NODE_HEALTH_DEGRADED"

        if (
            transition.kind
            is HealthTransitionKind.IMPROVED
        ):
            return "NODE_HEALTH_IMPROVED"

        if (
            transition.kind
            is HealthTransitionKind.RECOVERED
        ):
            return "NODE_HEALTH_RECOVERED"

        return "NODE_HEALTH_UNKNOWN"

    @staticmethod
    def _severity(
        transition: HealthTransition,
    ) -> EventSeverity:
        if (
            transition.kind
            is HealthTransitionKind.RECOVERED
        ):
            return EventSeverity.INFO

        if (
            transition.kind
            is HealthTransitionKind.IMPROVED
        ):
            return EventSeverity.NOTICE

        if (
            transition.kind
            is HealthTransitionKind.UNKNOWN
        ):
            return EventSeverity.NOTICE

        current = transition.current.state

        if current is NodeHealthState.CRITICAL:
            return EventSeverity.CRITICAL

        if current is NodeHealthState.DEGRADED:
            return EventSeverity.ERROR

        return EventSeverity.WARNING

    @staticmethod
    def _title(
        transition: HealthTransition,
    ) -> str:
        return (
            "Node health changed to "
            f"{transition.current.state.value}"
        )

    @staticmethod
    def _description(
        transition: HealthTransition,
    ) -> str:
        return (
            "Node health transitioned from "
            f"{transition.previous.state.value} "
            "to "
            f"{transition.current.state.value}"
        )

    @staticmethod
    def _validate_timestamp(
        timestamp: datetime,
    ) -> None:
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
