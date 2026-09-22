"""Operational projection of multimedia session evidence.

Physical MediaMTX evidence is preserved unchanged.

The projector derives an operational view in which explicitly identified
internal media observers do not constitute client demand.

Internal reader correlation uses the proven MediaMTX relationship:

    ActiveSession.session_id == MediaReader.reader_id

No classification is inferred from localhost, protocol, port, path, or
signal name.
"""

from __future__ import annotations

from dataclasses import replace

from app.domain.sessions import SessionSnapshot
from app.domain.streaming.models import MediaMTXSnapshot


INTERNAL_MEDIA_OBSERVER_USER_AGENT = "EBP-MediaObserver/1"


class SessionOperationalProjector:
    """Derive operational session and reader views from raw evidence."""

    def __init__(
        self,
        *,
        internal_observer_user_agent: str,
    ) -> None:
        if not isinstance(internal_observer_user_agent, str):
            raise TypeError(
                "internal_observer_user_agent must be a str"
            )

        marker = internal_observer_user_agent.strip()

        if not marker:
            raise ValueError(
                "internal_observer_user_agent must not be empty"
            )

        self._internal_observer_user_agent = marker

    def project(
        self,
        *,
        session_snapshot: SessionSnapshot,
        media_snapshot: MediaMTXSnapshot,
    ) -> tuple[SessionSnapshot, MediaMTXSnapshot]:
        """Return operational projections without modifying raw snapshots."""

        if not isinstance(session_snapshot, SessionSnapshot):
            raise TypeError(
                "session_snapshot must be a SessionSnapshot"
            )

        if not isinstance(media_snapshot, MediaMTXSnapshot):
            raise TypeError(
                "media_snapshot must be a MediaMTXSnapshot"
            )

        internal_session_ids = frozenset(
            session.session_id
            for session in session_snapshot.sessions
            if (
                session.user_agent
                == self._internal_observer_user_agent
            )
        )

        operational_sessions = replace(
            session_snapshot,
            sessions=tuple(
                session
                for session in session_snapshot.sessions
                if session.session_id not in internal_session_ids
            ),
        )

        operational_paths = tuple(
            replace(
                media_path,
                readers=tuple(
                    reader
                    for reader in media_path.readers
                    if reader.reader_id not in internal_session_ids
                ),
            )
            for media_path in media_snapshot.paths
        )

        operational_media = replace(
            media_snapshot,
            paths=operational_paths,
        )

        return (
            operational_sessions,
            operational_media,
        )
