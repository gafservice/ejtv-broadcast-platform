"""Multimedia session transition detection for the NOC.

ENG-013B — Node SDK

SessionTransitionDetector compares consecutive SessionSnapshot values and
classifies session lifecycle changes.

A session is identified exclusively by session_id.

It does not persist events, raise alarms or modify session state.
Its only responsibility is to detect CONNECTED and DISCONNECTED
transitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.sessions import (
    ActiveSession,
    SessionSnapshot,
)


class SessionTransitionKind(str, Enum):
    """Classification of a multimedia session transition."""

    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SessionTransition:
    """Immutable description of one session lifecycle transition."""

    session: ActiveSession
    kind: SessionTransitionKind

    def __post_init__(self) -> None:
        if not isinstance(
            self.session,
            ActiveSession,
        ):
            raise TypeError(
                "session must be an ActiveSession"
            )

        if not isinstance(
            self.kind,
            SessionTransitionKind,
        ):
            raise TypeError(
                "kind must be a SessionTransitionKind"
            )


class SessionTransitionDetector:
    """Detect lifecycle changes between SessionSnapshot values."""

    def detect(
        self,
        previous: SessionSnapshot | None,
        current: SessionSnapshot,
    ) -> tuple[SessionTransition, ...]:
        """Return CONNECTED and DISCONNECTED session transitions."""

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

        # The first observation establishes the baseline.
        # Existing sessions must not be reported as newly connected.
        if previous is None:
            return ()

        previous_by_id = {
            session.session_id: session
            for session in previous.sessions
        }

        current_by_id = {
            session.session_id: session
            for session in current.sessions
        }

        disconnected_ids = (
            previous_by_id.keys()
            - current_by_id.keys()
        )

        connected_ids = (
            current_by_id.keys()
            - previous_by_id.keys()
        )

        transitions: list[SessionTransition] = []

        for session_id in sorted(disconnected_ids):
            transitions.append(
                SessionTransition(
                    session=previous_by_id[session_id],
                    kind=SessionTransitionKind.DISCONNECTED,
                )
            )

        for session_id in sorted(connected_ids):
            transitions.append(
                SessionTransition(
                    session=current_by_id[session_id],
                    kind=SessionTransitionKind.CONNECTED,
                )
            )

        return tuple(transitions)
