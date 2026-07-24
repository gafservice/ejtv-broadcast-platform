"""Pruebas para el servicio de sesiones multimedia."""

from datetime import UTC, datetime

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionQuality,
    SessionRole,
    SessionSnapshot,
)
from app.services.session_service import SessionService


CAPTURED_AT = datetime(2026, 7, 24, 20, 0, tzinfo=UTC)
CONNECTED_AT = datetime(2026, 7, 24, 19, 0, tzinfo=UTC)


def build_session(
    *,
    session_id: str,
    path: str | None = "channel-1",
    protocol: SessionProtocol = SessionProtocol.SRT,
    role: SessionRole = SessionRole.READER,
    quality: SessionQuality = SessionQuality.EXCELLENT,
    remote_ip: str = "203.0.113.10",
    remote_port: int = 9000,
    bitrate_receive_mbps: float | None = 0.0,
    bitrate_send_mbps: float | None = 4.0,
) -> ActiveSession:
    """Construye una sesión válida para pruebas."""

    return ActiveSession(
        session_id=session_id,
        protocol=protocol,
        role=role,
        state=(
            "publish"
            if role is SessionRole.PUBLISHER
            else "read"
        ),
        remote_ip=remote_ip,
        remote_port=remote_port,
        path=path,
        connected_since=CONNECTED_AT,
        bitrate_receive_mbps=bitrate_receive_mbps,
        bitrate_send_mbps=bitrate_send_mbps,
        quality=quality,
    )


def build_snapshot(
    *sessions: ActiveSession,
) -> SessionSnapshot:
    """Construye un snapshot con una fecha fija."""

    return SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=tuple(sessions),
    )


def test_measure_empty_snapshot() -> None:
    measurement = SessionService().measure(
        build_snapshot()
    )

    assert measurement.captured_at == CAPTURED_AT
    assert measurement.sessions == ()
    assert measurement.paths == ()
    assert measurement.total_sessions == 0
    assert measurement.reader_count == 0
    assert measurement.publisher_count == 0
    assert measurement.unknown_role_count == 0
    assert measurement.degraded_session_count == 0
    assert measurement.critical_session_count == 0
    assert measurement.total_inbound_bitrate_mbps == 0.0
    assert measurement.total_outbound_bitrate_mbps == 0.0
    assert measurement.worst_quality is SessionQuality.UNKNOWN
    assert measurement.protocols == ()


def test_measure_counts_roles() -> None:
    reader = build_session(
        session_id="reader",
        role=SessionRole.READER,
    )
    publisher = build_session(
        session_id="publisher",
        role=SessionRole.PUBLISHER,
    )
    unknown = build_session(
        session_id="unknown",
        role=SessionRole.UNKNOWN,
    )

    measurement = SessionService().measure(
        build_snapshot(reader, publisher, unknown)
    )

    assert measurement.total_sessions == 3
    assert measurement.reader_count == 1
    assert measurement.publisher_count == 1
    assert measurement.unknown_role_count == 1


def test_measure_sums_inbound_and_outbound_bitrate() -> None:
    publisher = build_session(
        session_id="publisher",
        role=SessionRole.PUBLISHER,
        bitrate_receive_mbps=5.5,
        bitrate_send_mbps=0.0,
    )
    reader_one = build_session(
        session_id="reader-1",
        bitrate_receive_mbps=0.0,
        bitrate_send_mbps=4.0,
    )
    reader_two = build_session(
        session_id="reader-2",
        bitrate_receive_mbps=None,
        bitrate_send_mbps=3.5,
    )

    measurement = SessionService().measure(
        build_snapshot(
            publisher,
            reader_one,
            reader_two,
        )
    )

    assert measurement.total_inbound_bitrate_mbps == pytest.approx(5.5)
    assert measurement.total_outbound_bitrate_mbps == pytest.approx(7.5)


def test_measure_counts_degraded_and_critical_sessions() -> None:
    sessions = (
        build_session(
            session_id="excellent",
            quality=SessionQuality.EXCELLENT,
        ),
        build_session(
            session_id="good",
            quality=SessionQuality.GOOD,
        ),
        build_session(
            session_id="fair",
            quality=SessionQuality.FAIR,
        ),
        build_session(
            session_id="poor",
            quality=SessionQuality.POOR,
        ),
        build_session(
            session_id="critical",
            quality=SessionQuality.CRITICAL,
        ),
        build_session(
            session_id="unknown",
            quality=SessionQuality.UNKNOWN,
        ),
    )

    measurement = SessionService().measure(
        build_snapshot(*sessions)
    )

    assert measurement.degraded_session_count == 3
    assert measurement.critical_session_count == 1
    assert measurement.has_degraded_sessions is True
    assert measurement.has_critical_sessions is True


def test_measure_resolves_worst_global_quality() -> None:
    measurement = SessionService().measure(
        build_snapshot(
            build_session(
                session_id="good",
                quality=SessionQuality.GOOD,
            ),
            build_session(
                session_id="poor",
                quality=SessionQuality.POOR,
            ),
            build_session(
                session_id="fair",
                quality=SessionQuality.FAIR,
            ),
        )
    )

    assert measurement.worst_quality is SessionQuality.POOR


def test_unknown_quality_does_not_override_known_quality() -> None:
    measurement = SessionService().measure(
        build_snapshot(
            build_session(
                session_id="unknown",
                quality=SessionQuality.UNKNOWN,
            ),
            build_session(
                session_id="good",
                quality=SessionQuality.GOOD,
            ),
        )
    )

    assert measurement.worst_quality is SessionQuality.GOOD


def test_all_unknown_qualities_resolve_to_unknown() -> None:
    measurement = SessionService().measure(
        build_snapshot(
            build_session(
                session_id="unknown-1",
                quality=SessionQuality.UNKNOWN,
            ),
            build_session(
                session_id="unknown-2",
                quality=SessionQuality.UNKNOWN,
            ),
        )
    )

    assert measurement.worst_quality is SessionQuality.UNKNOWN


def test_measure_collects_protocols() -> None:
    measurement = SessionService().measure(
        build_snapshot(
            build_session(
                session_id="srt",
                protocol=SessionProtocol.SRT,
            ),
            build_session(
                session_id="webrtc",
                protocol=SessionProtocol.WEBRTC,
            ),
            build_session(
                session_id="rtmp",
                protocol=SessionProtocol.RTMP,
            ),
        )
    )

    assert measurement.protocols == (
        SessionProtocol.RTMP,
        SessionProtocol.SRT,
        SessionProtocol.WEBRTC,
    )


def test_measure_groups_sessions_by_path() -> None:
    measurement = SessionService().measure(
        build_snapshot(
            build_session(
                session_id="channel-a-reader",
                path="channel-a",
                role=SessionRole.READER,
                bitrate_send_mbps=4.0,
            ),
            build_session(
                session_id="channel-a-publisher",
                path="channel-a",
                role=SessionRole.PUBLISHER,
                bitrate_receive_mbps=5.0,
                bitrate_send_mbps=0.0,
            ),
            build_session(
                session_id="channel-b-reader",
                path="channel-b",
                role=SessionRole.READER,
                quality=SessionQuality.FAIR,
                bitrate_send_mbps=3.0,
            ),
        )
    )

    assert len(measurement.paths) == 2

    channel_a = measurement.paths[0]
    channel_b = measurement.paths[1]

    assert channel_a.path == "channel-a"
    assert channel_a.session_count == 2
    assert channel_a.reader_count == 1
    assert channel_a.publisher_count == 1
    assert channel_a.inbound_bitrate_mbps == pytest.approx(5.0)
    assert channel_a.outbound_bitrate_mbps == pytest.approx(4.0)
    assert channel_a.degraded_session_count == 0
    assert channel_a.worst_quality is SessionQuality.EXCELLENT

    assert channel_b.path == "channel-b"
    assert channel_b.session_count == 1
    assert channel_b.reader_count == 1
    assert channel_b.publisher_count == 0
    assert channel_b.outbound_bitrate_mbps == pytest.approx(3.0)
    assert channel_b.degraded_session_count == 1
    assert channel_b.worst_quality is SessionQuality.FAIR


def test_measure_groups_missing_path_under_reserved_label() -> None:
    measurement = SessionService().measure(
        build_snapshot(
            build_session(
                session_id="without-path",
                path=None,
            )
        )
    )

    assert len(measurement.paths) == 1
    assert measurement.paths[0].path == SessionService.UNASSIGNED_PATH
    assert measurement.paths[0].session_count == 1


def test_sessions_are_sorted_with_worst_quality_first() -> None:
    excellent = build_session(
        session_id="excellent",
        path="channel-a",
        quality=SessionQuality.EXCELLENT,
    )
    critical = build_session(
        session_id="critical",
        path="channel-z",
        quality=SessionQuality.CRITICAL,
    )
    fair = build_session(
        session_id="fair",
        path="channel-b",
        quality=SessionQuality.FAIR,
    )

    measurement = SessionService().measure(
        build_snapshot(excellent, critical, fair)
    )

    assert tuple(
        session.session_id
        for session in measurement.sessions
    ) == (
        "critical",
        "fair",
        "excellent",
    )


def test_sessions_with_equal_quality_are_sorted_deterministically() -> None:
    second = build_session(
        session_id="second",
        path="channel-b",
        remote_ip="203.0.113.20",
    )
    first = build_session(
        session_id="first",
        path="channel-a",
        remote_ip="203.0.113.10",
    )

    measurement = SessionService().measure(
        build_snapshot(second, first)
    )

    assert tuple(
        session.session_id
        for session in measurement.sessions
    ) == (
        "first",
        "second",
    )


def test_measure_does_not_modify_original_snapshot() -> None:
    second = build_session(
        session_id="second",
        path="channel-b",
    )
    first = build_session(
        session_id="first",
        path="channel-a",
    )

    snapshot = build_snapshot(second, first)

    measurement = SessionService().measure(snapshot)

    assert snapshot.sessions == (second, first)
    assert measurement.sessions == (first, second)
