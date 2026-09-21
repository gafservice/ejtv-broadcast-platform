"""Stream Health transition to operational event mapping.

ENG-013B — Stream Health Contract Block 4

StreamingHealthTransitionEventFactory converts one already detected
StreamingHealthTransition into one immutable EventRecord.

It does not detect transitions, persist events, raise alarms, or modify
Stream Health state.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.streaming_health_transition_detector import (
    StreamingHealthTransition,
)


class StreamingHealthTransitionEventFactory:
    """Create EventRecord objects from Stream Health transitions."""

    def create(
        self,
        *,
        transition: StreamingHealthTransition,
        source: NodeInstanceId,
        timestamp: datetime,
    ) -> EventRecord:
        """Create one immutable operational Stream Health event."""

        if not isinstance(
            transition,
            StreamingHealthTransition,
        ):
            raise TypeError(
                "transition must be a StreamingHealthTransition"
            )

        if not isinstance(source, NodeInstanceId):
            raise TypeError(
                "source must be a NodeInstanceId"
            )

        self._validate_timestamp(timestamp)

        return EventRecord(
            event_id=self._event_id(),
            event_type=self._event_type(transition),
            severity=self._severity(transition),
            timestamp=timestamp,
            source=source,
            title=self._title(transition),
            description=self._description(transition),
            attributes=self._attributes(transition),
        )

    @classmethod
    def _attributes(
        cls,
        transition: StreamingHealthTransition,
    ) -> dict[str, str]:
        """Build durable attributes for one stream-health transition."""

        attributes = {
            "previous": transition.previous.status.value,
            "current": transition.current.status.value,
            "transition": transition.kind.value,
        }

        cause = cls._single_connection_cause(transition)

        if cause is None:
            return attributes

        previous_connection, current_connection = cause

        attributes.update(
            {
                "protocol": "SRT",
                "path": current_connection.path_name,
                "connection_id": current_connection.connection_id,
                "connection_state": current_connection.state,
                "cause_previous": previous_connection.status.value,
                "cause_current": current_connection.status.value,
            }
        )

        if current_connection.remote_address is not None:
            attributes["remote_address"] = (
                current_connection.remote_address
            )

        if current_connection.role is not None:
            attributes["role"] = current_connection.role

        return attributes

    @staticmethod
    def _single_connection_cause(
        transition: StreamingHealthTransition,
    ):
        """Return one changed SRT connection when attribution is unique."""

        previous_connections = {
            connection.connection_id: connection
            for path in transition.previous.paths
            for connection in path.connections
        }

        current_connections = {
            connection.connection_id: connection
            for path in transition.current.paths
            for connection in path.connections
        }

        changed = tuple(
            (
                previous_connection,
                current_connections[connection_id],
            )
            for connection_id, previous_connection
            in previous_connections.items()
            if connection_id in current_connections
            and (
                previous_connection.status
                is not current_connections[connection_id].status
            )
        )

        if len(changed) != 1:
            return None

        previous_connection, current_connection = changed[0]

        if (
            previous_connection.path_name
            != current_connection.path_name
        ):
            return None

        return previous_connection, current_connection

    @staticmethod
    def _event_id() -> str:
        return f"evt-{uuid4().hex}"

    @staticmethod
    def _event_type(
        transition: StreamingHealthTransition,
    ) -> str:
        if transition.kind is HealthTransitionKind.RECOVERED:
            return "STREAM_HEALTH_RECOVERED"

        if transition.kind is HealthTransitionKind.IMPROVED:
            return "STREAM_HEALTH_IMPROVED"

        if transition.kind is HealthTransitionKind.UNKNOWN:
            return "STREAM_HEALTH_UNKNOWN"

        return "STREAM_HEALTH_DEGRADED"

    @staticmethod
    def _severity(
        transition: StreamingHealthTransition,
    ) -> EventSeverity:
        if transition.kind is HealthTransitionKind.RECOVERED:
            return EventSeverity.INFO

        if transition.kind in {
            HealthTransitionKind.IMPROVED,
            HealthTransitionKind.UNKNOWN,
        }:
            return EventSeverity.NOTICE

        if transition.current.status.value == "CRITICAL":
            return EventSeverity.CRITICAL

        return EventSeverity.WARNING

    @staticmethod
    def _title(
        transition: StreamingHealthTransition,
    ) -> str:
        return (
            "Stream Health changed to "
            f"{transition.current.status.value}"
        )

    @staticmethod
    def _description(
        transition: StreamingHealthTransition,
    ) -> str:
        return (
            "Stream Health changed from "
            f"{transition.previous.status.value} "
            f"to {transition.current.status.value} "
            f"({transition.kind.value})."
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
