from datetime import UTC, datetime

from app.domain.streaming.models import (
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaReader,
    MediaSource,
)
from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.noc.services.session_operational_projector import (
    SessionOperationalProjector,
)


NOW = datetime(
    2026,
    9,
    22,
    16,
    0,
    tzinfo=UTC,
)

INTERNAL_USER_AGENT = "EBP-MediaObserver/1"


def build_session(
    *,
    session_id: str,
    protocol: SessionProtocol,
    user_agent: str | None = None,
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=protocol,
        role=SessionRole.READER,
        state="read",
        remote_ip="127.0.0.1",
        remote_port=50000,
        path="impact",
        connected_since=NOW,
        user_agent=user_agent,
    )


def build_path(
    *readers: MediaReader,
) -> MediaPath:
    return MediaPath(
        name="impact",
        configuration_name="impact",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(
            source_type="srtSource",
        ),
        readers=tuple(readers),
    )


def build_session_snapshot(
    *sessions: ActiveSession,
) -> SessionSnapshot:
    return SessionSnapshot(
        captured_at=NOW,
        sessions=tuple(sessions),
    )


def build_media_snapshot(
    path: MediaPath,
) -> MediaMTXSnapshot:
    return MediaMTXSnapshot(
        captured_at=NOW,
        paths=(path,),
        reported_item_count=1,
        reported_page_count=1,
    )


def test_internal_observer_is_excluded_from_operational_sessions() -> None:
    projector = SessionOperationalProjector(
        internal_observer_user_agent=INTERNAL_USER_AGENT,
    )

    internal = build_session(
        session_id="internal",
        protocol=SessionProtocol.RTSP,
        user_agent=INTERNAL_USER_AGENT,
    )

    sessions, media = projector.project(
        session_snapshot=build_session_snapshot(internal),
        media_snapshot=build_media_snapshot(
            build_path(
                MediaReader(
                    reader_type="rtspSession",
                    reader_id="internal",
                ),
            )
        ),
    )

    assert sessions.sessions == ()
    assert media.paths[0].reader_count == 0


def test_real_reader_remains_operational_beside_internal_observer() -> None:
    projector = SessionOperationalProjector(
        internal_observer_user_agent=INTERNAL_USER_AGENT,
    )

    internal = build_session(
        session_id="internal",
        protocol=SessionProtocol.RTSP,
        user_agent=INTERNAL_USER_AGENT,
    )

    real = build_session(
        session_id="real",
        protocol=SessionProtocol.WEBRTC,
    )

    sessions, media = projector.project(
        session_snapshot=build_session_snapshot(
            internal,
            real,
        ),
        media_snapshot=build_media_snapshot(
            build_path(
                MediaReader(
                    reader_type="rtspSession",
                    reader_id="internal",
                ),
                MediaReader(
                    reader_type="webRTCSession",
                    reader_id="real",
                ),
            )
        ),
    )

    assert tuple(
        session.session_id
        for session in sessions.sessions
    ) == ("real",)

    assert tuple(
        reader.reader_id
        for reader in media.paths[0].readers
    ) == ("real",)

    assert media.paths[0].reader_count == 1


def test_unmarked_rtsp_reader_remains_operational() -> None:
    projector = SessionOperationalProjector(
        internal_observer_user_agent=INTERNAL_USER_AGENT,
    )

    real_rtsp = build_session(
        session_id="real-rtsp",
        protocol=SessionProtocol.RTSP,
        user_agent="External-RTSP-Client/1",
    )

    sessions, media = projector.project(
        session_snapshot=build_session_snapshot(real_rtsp),
        media_snapshot=build_media_snapshot(
            build_path(
                MediaReader(
                    reader_type="rtspSession",
                    reader_id="real-rtsp",
                ),
            )
        ),
    )

    assert tuple(
        session.session_id
        for session in sessions.sessions
    ) == ("real-rtsp",)

    assert media.paths[0].reader_count == 1


def test_localhost_without_marker_remains_operational() -> None:
    projector = SessionOperationalProjector(
        internal_observer_user_agent=INTERNAL_USER_AGENT,
    )

    local_reader = build_session(
        session_id="local-real",
        protocol=SessionProtocol.RTSP,
    )

    sessions, media = projector.project(
        session_snapshot=build_session_snapshot(local_reader),
        media_snapshot=build_media_snapshot(
            build_path(
                MediaReader(
                    reader_type="rtspSession",
                    reader_id="local-real",
                ),
            )
        ),
    )

    assert tuple(
        session.session_id
        for session in sessions.sessions
    ) == ("local-real",)

    assert media.paths[0].reader_count == 1


def test_raw_snapshots_are_not_modified() -> None:
    projector = SessionOperationalProjector(
        internal_observer_user_agent=INTERNAL_USER_AGENT,
    )

    internal = build_session(
        session_id="internal",
        protocol=SessionProtocol.RTSP,
        user_agent=INTERNAL_USER_AGENT,
    )

    raw_sessions = build_session_snapshot(internal)

    raw_media = build_media_snapshot(
        build_path(
            MediaReader(
                reader_type="rtspSession",
                reader_id="internal",
            ),
        )
    )

    operational_sessions, operational_media = projector.project(
        session_snapshot=raw_sessions,
        media_snapshot=raw_media,
    )

    assert raw_sessions.sessions == (internal,)
    assert raw_media.paths[0].reader_count == 1

    assert operational_sessions is not raw_sessions
    assert operational_media is not raw_media

    assert operational_sessions.sessions == ()
    assert operational_media.paths[0].reader_count == 0


def test_unmatched_media_reader_remains_operational() -> None:
    projector = SessionOperationalProjector(
        internal_observer_user_agent=INTERNAL_USER_AGENT,
    )

    captured_at = datetime(
        2026,
        9,
        22,
        17,
        0,
        tzinfo=UTC,
    )

    raw_sessions = SessionSnapshot(
        captured_at=captured_at,
        sessions=(),
    )

    unmatched_reader = MediaReader(
        reader_type="rtspSession",
        reader_id="unmatched-reader",
    )

    raw_path = MediaPath(
        name="impact",
        configuration_name="impact",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(
            source_type="srtSource",
        ),
        readers=(
            unmatched_reader,
        ),
    )

    raw_media = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(
            raw_path,
        ),
        reported_item_count=1,
        reported_page_count=1,
    )

    operational_sessions, operational_media = (
        projector.project(
            session_snapshot=raw_sessions,
            media_snapshot=raw_media,
        )
    )

    assert operational_sessions.sessions == ()

    assert len(operational_media.paths) == 1

    assert operational_media.paths[0].readers == (
        unmatched_reader,
    )

    assert operational_media.paths[0].reader_count == 1

    assert raw_path.reader_count == 1
