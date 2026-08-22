"""Session transition to operational event mapping for the NOC.

ENG-013B — Node SDK

SessionTransitionEventFactory converts a multimedia session lifecycle
transition into an immutable EventRecord.

It does not detect transitions, persist events, raise alarms or modify
session state.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.session_transition_detector import (
    SessionTransition,
    SessionTransitionKind,
)


class SessionTransitionEventFactory:
    """Create EventRecord objects from multimedia session transitions."""

    def create(
        self,
        *,
        transition: SessionTransition,
        source: NodeInstanceId,
        timestamp: datetime,
    ) -> EventRecord:
        """Create one immutable operational event."""

        if not isinstance(
            transition,
            SessionTransition,
        ):
            raise TypeError(
                "transition must be a SessionTransition"
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

        session = transition.session

        return EventRecord(
            event_id=self._event_id(),
            event_type=self._event_type(
                transition
            ),
            severity=self._severity(
                transition
            ),
            timestamp=timestamp,
            source=source,
            title=self._title(
                transition
            ),
            description=self._description(
                transition
            ),
            attributes={
                "session_id": session.session_id,
                "protocol": session.protocol.value,
                "role": session.role.value,
                "path": self._optional_text(
                    session.path
                ),
                "remote_ip": session.remote_ip,
                "remote_port": self._optional_text(
                    session.remote_port
                ),
                "remote_address": session.remote_address,
                "username": self._optional_text(
                    session.username
                ),
            },
        )

    @staticmethod
    def _optional_text(
        value: object | None,
    ) -> str:
        """Normalize optional event attributes to strings."""

        if value is None:
            return ""

        return str(value)

    @staticmethod
    def _event_id() -> str:
        return f"evt-{uuid4().hex}"

    @staticmethod
    def _event_type(
        transition: SessionTransition,
    ) -> str:
        if (
            transition.kind
            is SessionTransitionKind.CONNECTED
        ):
            return "SESSION_CONNECTED"

        return "SESSION_DISCONNECTED"

    @staticmethod
    def _severity(
        transition: SessionTransition,
    ) -> EventSeverity:
        if (
            transition.kind
            is SessionTransitionKind.CONNECTED
        ):
            return EventSeverity.INFO

        return EventSeverity.NOTICE

    @staticmethod
    def _title(
        transition: SessionTransition,
    ) -> str:
        session = transition.session

        action = (
            "connected"
            if transition.kind
            is SessionTransitionKind.CONNECTED
            else "disconnected"
        )

        path = (
            session.path
            if session.path is not None
            else "-"
        )

        return (
            f"{session.protocol.value} "
            f"{session.role.value.lower()} "
            f"{action} on {path}"
        )

    @staticmethod
    def _description(
        transition: SessionTransition,
    ) -> str:
        session = transition.session

        action = (
            "connected to"
            if transition.kind
            is SessionTransitionKind.CONNECTED
            else "disconnected from"
        )

        path = (
            session.path
            if session.path is not None
            else "-"
        )

        return (
            f"Session {session.session_id!r} "
            f"from {session.remote_address} "
            f"{action} path {path!r} "
            f"using {session.protocol.value} "
            f"as {session.role.value}."
        )

    @staticmethod
    def _validate_timestamp(
        timestamp: datetime,
    ) -> None:
        if not isinstance(
            timestamp,
            datetime,
        ):
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
