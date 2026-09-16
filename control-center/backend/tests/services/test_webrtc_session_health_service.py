"""Tests del servicio temporal especializado de salud WebRTC."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.domain.streaming import HealthStatus
from app.services.webrtc_session_health_service import (
    WebRTCSessionHealthService,
)


CAPTURED_AT = datetime(2026, 9, 16, 8, 56, 2, tzinfo=UTC)


def make_session(
    *,
    session_id: str = "webrtc-session-1",
    protocol: SessionProtocol = SessionProtocol.WEBRTC,
    role: SessionRole = SessionRole.READER,
    state: str = "read",
    path: str | None = "impact",
    connected_since: datetime = CAPTURED_AT,
    bytes_received: int = 0,
    bytes_sent: int = 0,
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=protocol,
        role=role,
        state=state,
        remote_ip="192.168.33.234",
        remote_port=65184,
        path=path,
        connected_since=connected_since,
        bytes_received=bytes_received,
        bytes_sent=bytes_sent,
    )


def snapshot(
    captured_at: datetime,
    *sessions: ActiveSession,
) -> SessionSnapshot:
    return SessionSnapshot(
        captured_at=captured_at,
        sessions=tuple(sessions),
    )


def test_first_webrtc_observation_is_unknown_without_temporal_evidence() -> None:
    current = snapshot(
        CAPTURED_AT,
        make_session(bytes_sent=331_579_947),
    )

    health = WebRTCSessionHealthService().build(
        previous_snapshot=None,
        current_snapshot=current,
    )

    assert len(health) == 1

    session = health[0]
    assert session.session_id == "webrtc-session-1"
    assert session.path_name == "impact"
    assert session.state == "read"
    assert session.effective_delta_bytes is None
    assert session.effective_bitrate_mbps is None
    assert session.status is HealthStatus.UNKNOWN


def test_webrtc_reader_uses_sent_byte_delta_as_activity_evidence() -> None:
    previous = snapshot(
        CAPTURED_AT,
        make_session(bytes_sent=331_579_947),
    )
    current = snapshot(
        CAPTURED_AT + timedelta(seconds=10),
        make_session(bytes_sent=339_141_532),
    )

    session = WebRTCSessionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )[0]

    assert session.effective_delta_bytes == 7_561_585
    assert session.effective_bitrate_mbps == pytest.approx(6.049268)
    assert session.status is HealthStatus.HEALTHY


def test_webrtc_publisher_uses_received_byte_delta_as_activity_evidence() -> None:
    previous = snapshot(
        CAPTURED_AT,
        make_session(
            role=SessionRole.PUBLISHER,
            state="publish",
            bytes_received=1_000_000,
        ),
    )
    current = snapshot(
        CAPTURED_AT + timedelta(seconds=10),
        make_session(
            role=SessionRole.PUBLISHER,
            state="publish",
            bytes_received=2_500_000,
        ),
    )

    session = WebRTCSessionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )[0]

    assert session.effective_delta_bytes == 1_500_000
    assert session.effective_bitrate_mbps == pytest.approx(1.2)
    assert session.status is HealthStatus.HEALTHY


def test_webrtc_zero_effective_delta_remains_unknown() -> None:
    previous = snapshot(
        CAPTURED_AT,
        make_session(bytes_sent=2_000_000),
    )
    current = snapshot(
        CAPTURED_AT + timedelta(seconds=5),
        make_session(bytes_sent=2_000_000),
    )

    session = WebRTCSessionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )[0]

    assert session.effective_delta_bytes is None
    assert session.effective_bitrate_mbps is None
    assert session.status is HealthStatus.UNKNOWN


def test_webrtc_counter_reset_remains_unknown() -> None:
    previous = snapshot(
        CAPTURED_AT,
        make_session(bytes_sent=2_000_000),
    )
    current = snapshot(
        CAPTURED_AT + timedelta(seconds=5),
        make_session(bytes_sent=1_000_000),
    )

    session = WebRTCSessionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )[0]

    assert session.effective_delta_bytes is None
    assert session.effective_bitrate_mbps is None
    assert session.status is HealthStatus.UNKNOWN


@pytest.mark.parametrize("interval_seconds", [0, -5])
def test_webrtc_invalid_temporal_interval_remains_unknown(
    interval_seconds: int,
) -> None:
    previous = snapshot(
        CAPTURED_AT,
        make_session(bytes_sent=1_000_000),
    )
    current = snapshot(
        CAPTURED_AT + timedelta(seconds=interval_seconds),
        make_session(bytes_sent=2_000_000),
    )

    session = WebRTCSessionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )[0]

    assert session.effective_delta_bytes is None
    assert session.effective_bitrate_mbps is None
    assert session.status is HealthStatus.UNKNOWN


def test_webrtc_identity_change_does_not_reuse_previous_evidence() -> None:
    previous = snapshot(
        CAPTURED_AT,
        make_session(
            connected_since=CAPTURED_AT,
            bytes_sent=1_000_000,
        ),
    )
    current = snapshot(
        CAPTURED_AT + timedelta(seconds=5),
        make_session(
            connected_since=CAPTURED_AT + timedelta(seconds=1),
            bytes_sent=2_000_000,
        ),
    )

    session = WebRTCSessionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )[0]

    assert session.effective_delta_bytes is None
    assert session.effective_bitrate_mbps is None
    assert session.status is HealthStatus.UNKNOWN


def test_webrtc_unknown_role_does_not_infer_effective_direction() -> None:
    previous = snapshot(
        CAPTURED_AT,
        make_session(
            role=SessionRole.UNKNOWN,
            state="unknown",
            bytes_received=1_000_000,
            bytes_sent=1_000_000,
        ),
    )
    current = snapshot(
        CAPTURED_AT + timedelta(seconds=5),
        make_session(
            role=SessionRole.UNKNOWN,
            state="unknown",
            bytes_received=2_000_000,
            bytes_sent=2_000_000,
        ),
    )

    session = WebRTCSessionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )[0]

    assert session.effective_delta_bytes is None
    assert session.effective_bitrate_mbps is None
    assert session.status is HealthStatus.UNKNOWN


def test_non_webrtc_sessions_and_webrtc_without_path_are_not_projected() -> None:
    current = snapshot(
        CAPTURED_AT,
        make_session(
            session_id="rtsp-1",
            protocol=SessionProtocol.RTSP,
        ),
        make_session(
            session_id="webrtc-no-path",
            path=None,
        ),
    )

    health = WebRTCSessionHealthService().build(
        previous_snapshot=None,
        current_snapshot=current,
    )

    assert health == ()
