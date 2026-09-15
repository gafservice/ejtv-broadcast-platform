"""Tests del servicio temporal especializado de salud HLS."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.domain.streaming import HealthStatus
from app.services.hls_session_health_service import (
    HLSSessionHealthService,
)


CAPTURED_AT = datetime(2026, 9, 15, 8, 30, 0, tzinfo=UTC)


def make_session(
    *,
    session_id: str = "hls-session-1",
    protocol: SessionProtocol = SessionProtocol.HLS,
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
        remote_ip="127.0.0.1",
        remote_port=42176,
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


def test_first_hls_observation_is_unknown_without_temporal_evidence() -> None:
    current = snapshot(
        CAPTURED_AT,
        make_session(bytes_sent=2_000_000),
    )

    health = HLSSessionHealthService().build(
        previous_snapshot=None,
        current_snapshot=current,
    )

    assert len(health) == 1

    session = health[0]
    assert session.session_id == "hls-session-1"
    assert session.path_name == "impact"
    assert session.state == "read"
    assert session.effective_delta_bytes is None
    assert session.effective_bitrate_mbps is None
    assert session.status is HealthStatus.UNKNOWN


def test_hls_reader_uses_sent_byte_delta_as_activity_evidence() -> None:
    previous = snapshot(
        CAPTURED_AT,
        make_session(bytes_sent=2_000_000),
    )
    current = snapshot(
        CAPTURED_AT + timedelta(seconds=5),
        make_session(bytes_sent=5_000_000),
    )

    session = HLSSessionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )[0]

    assert session.effective_delta_bytes == 3_000_000
    assert session.effective_bitrate_mbps == pytest.approx(4.8)
    assert session.status is HealthStatus.HEALTHY


def test_hls_zero_effective_delta_remains_unknown() -> None:
    previous = snapshot(
        CAPTURED_AT,
        make_session(bytes_sent=2_000_000),
    )
    current = snapshot(
        CAPTURED_AT + timedelta(seconds=5),
        make_session(bytes_sent=2_000_000),
    )

    session = HLSSessionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )[0]

    assert session.effective_delta_bytes is None
    assert session.effective_bitrate_mbps is None
    assert session.status is HealthStatus.UNKNOWN


def test_hls_counter_reset_remains_unknown() -> None:
    previous = snapshot(
        CAPTURED_AT,
        make_session(bytes_sent=2_000_000),
    )
    current = snapshot(
        CAPTURED_AT + timedelta(seconds=5),
        make_session(bytes_sent=1_000_000),
    )

    session = HLSSessionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )[0]

    assert session.effective_delta_bytes is None
    assert session.effective_bitrate_mbps is None
    assert session.status is HealthStatus.UNKNOWN


@pytest.mark.parametrize("interval_seconds", [0, -5])
def test_hls_invalid_temporal_interval_remains_unknown(
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

    session = HLSSessionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )[0]

    assert session.effective_delta_bytes is None
    assert session.effective_bitrate_mbps is None
    assert session.status is HealthStatus.UNKNOWN


def test_hls_identity_change_does_not_reuse_previous_evidence() -> None:
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

    session = HLSSessionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )[0]

    assert session.effective_delta_bytes is None
    assert session.effective_bitrate_mbps is None
    assert session.status is HealthStatus.UNKNOWN


def test_hls_non_reader_role_remains_unknown() -> None:
    previous = snapshot(
        CAPTURED_AT,
        make_session(
            role=SessionRole.UNKNOWN,
            state="unknown",
            bytes_sent=1_000_000,
        ),
    )
    current = snapshot(
        CAPTURED_AT + timedelta(seconds=5),
        make_session(
            role=SessionRole.UNKNOWN,
            state="unknown",
            bytes_sent=2_000_000,
        ),
    )

    session = HLSSessionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )[0]

    assert session.effective_delta_bytes is None
    assert session.effective_bitrate_mbps is None
    assert session.status is HealthStatus.UNKNOWN


def test_non_hls_sessions_and_hls_without_path_are_not_projected() -> None:
    current = snapshot(
        CAPTURED_AT,
        make_session(
            session_id="rtsp-1",
            protocol=SessionProtocol.RTSP,
        ),
        make_session(
            session_id="hls-no-path",
            path=None,
        ),
    )

    health = HLSSessionHealthService().build(
        previous_snapshot=None,
        current_snapshot=current,
    )

    assert health == ()
