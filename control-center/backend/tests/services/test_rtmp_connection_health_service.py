"""Tests del servicio temporal especializado de salud RTMP."""

from datetime import UTC, datetime, timedelta
import pytest


from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.domain.streaming import HealthStatus
from app.services.rtmp_connection_health_service import (
    RTMPConnectionHealthService,
)


CAPTURED_AT = datetime(2026, 9, 10, 10, 14, 52, tzinfo=UTC)


def test_first_rtmp_observation_is_unknown_without_temporal_evidence() -> None:
    current = SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=(
            ActiveSession(
                session_id="rtmp-publisher-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.PUBLISHER,
                state="publish",
                remote_ip="127.0.0.1",
                remote_port=58164,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=1_502_066,
                bytes_sent=3_467,
            ),
        ),
    )

    health = RTMPConnectionHealthService().build(
        previous_snapshot=None,
        current_snapshot=current,
    )

    assert len(health) == 1

    connection = health[0]
    assert connection.connection_id == "rtmp-publisher-1"
    assert connection.path_name == "rtmp-block8-lab"
    assert connection.state == "publish"
    assert connection.effective_delta_bytes is None
    assert connection.effective_bitrate_mbps is None
    assert connection.outbound_frames_discarded is None
    assert connection.status is HealthStatus.UNKNOWN


def test_rtmp_publisher_uses_received_byte_delta_as_activity_evidence() -> None:
    previous = SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=(
            ActiveSession(
                session_id="rtmp-publisher-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.PUBLISHER,
                state="publish",
                remote_ip="127.0.0.1",
                remote_port=58164,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=1_502_066,
                bytes_sent=3_467,
            ),
        ),
    )

    current = SessionSnapshot(
        captured_at=CAPTURED_AT + timedelta(seconds=10),
        sessions=(
            ActiveSession(
                session_id="rtmp-publisher-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.PUBLISHER,
                state="publish",
                remote_ip="127.0.0.1",
                remote_port=58164,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=2_945_099,
                bytes_sent=3_467,
            ),
        ),
    )

    health = RTMPConnectionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )

    assert len(health) == 1

    connection = health[0]
    assert connection.effective_delta_bytes == 1_443_033
    assert connection.effective_bitrate_mbps == pytest.approx(1.1544264)
    assert connection.status is HealthStatus.HEALTHY


def test_rtmp_reader_uses_sent_byte_delta_as_activity_evidence() -> None:
    previous = SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=(
            ActiveSession(
                session_id="rtmp-reader-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.READER,
                state="read",
                remote_ip="127.0.0.1",
                remote_port=58165,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=3_455,
                bytes_sent=619_443,
            ),
        ),
    )

    current = SessionSnapshot(
        captured_at=CAPTURED_AT + timedelta(seconds=10),
        sessions=(
            ActiveSession(
                session_id="rtmp-reader-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.READER,
                state="read",
                remote_ip="127.0.0.1",
                remote_port=58165,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=3_455,
                bytes_sent=2_062_661,
            ),
        ),
    )

    health = RTMPConnectionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )

    assert len(health) == 1

    connection = health[0]
    assert connection.effective_delta_bytes == 1_443_218
    assert connection.effective_bitrate_mbps == pytest.approx(1.1545744)
    assert connection.status is HealthStatus.HEALTHY


def test_rtmp_unknown_role_does_not_infer_effective_direction() -> None:
    previous = SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=(
            ActiveSession(
                session_id="rtmp-unknown-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.UNKNOWN,
                state="unknown",
                remote_ip="127.0.0.1",
                remote_port=58166,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=100_000,
                bytes_sent=200_000,
            ),
        ),
    )

    current = SessionSnapshot(
        captured_at=CAPTURED_AT + timedelta(seconds=10),
        sessions=(
            ActiveSession(
                session_id="rtmp-unknown-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.UNKNOWN,
                state="unknown",
                remote_ip="127.0.0.1",
                remote_port=58166,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=300_000,
                bytes_sent=500_000,
            ),
        ),
    )

    health = RTMPConnectionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )

    assert len(health) == 1

    connection = health[0]
    assert connection.effective_delta_bytes is None
    assert connection.effective_bitrate_mbps is None
    assert connection.status is HealthStatus.UNKNOWN


@pytest.mark.parametrize("interval_seconds", [0, -10])
def test_rtmp_invalid_temporal_interval_remains_unknown(
    interval_seconds: int,
) -> None:
    previous = SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=(
            ActiveSession(
                session_id="rtmp-publisher-invalid-time",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.PUBLISHER,
                state="publish",
                remote_ip="127.0.0.1",
                remote_port=58167,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=1_000_000,
                bytes_sent=3_467,
            ),
        ),
    )

    current = SessionSnapshot(
        captured_at=CAPTURED_AT + timedelta(seconds=interval_seconds),
        sessions=(
            ActiveSession(
                session_id="rtmp-publisher-invalid-time",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.PUBLISHER,
                state="publish",
                remote_ip="127.0.0.1",
                remote_port=58167,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=2_000_000,
                bytes_sent=3_467,
            ),
        ),
    )

    health = RTMPConnectionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )

    assert len(health) == 1

    connection = health[0]
    assert connection.effective_delta_bytes is None
    assert connection.effective_bitrate_mbps is None
    assert connection.status is HealthStatus.UNKNOWN


@pytest.mark.parametrize(
    ("role", "previous_received", "current_received", "previous_sent", "current_sent"),
    [
        (SessionRole.PUBLISHER, 2_000_000, 1_000_000, 3_467, 3_467),
        (SessionRole.READER, 3_455, 3_455, 2_000_000, 1_000_000),
    ],
)
def test_rtmp_counter_reset_remains_unknown(
    role: SessionRole,
    previous_received: int,
    current_received: int,
    previous_sent: int,
    current_sent: int,
) -> None:
    previous = SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=(
            ActiveSession(
                session_id="rtmp-reset-1",
                protocol=SessionProtocol.RTMP,
                role=role,
                state="publish" if role is SessionRole.PUBLISHER else "read",
                remote_ip="127.0.0.1",
                remote_port=58168,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=previous_received,
                bytes_sent=previous_sent,
            ),
        ),
    )

    current = SessionSnapshot(
        captured_at=CAPTURED_AT + timedelta(seconds=10),
        sessions=(
            ActiveSession(
                session_id="rtmp-reset-1",
                protocol=SessionProtocol.RTMP,
                role=role,
                state="publish" if role is SessionRole.PUBLISHER else "read",
                remote_ip="127.0.0.1",
                remote_port=58168,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=current_received,
                bytes_sent=current_sent,
            ),
        ),
    )

    health = RTMPConnectionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )

    assert len(health) == 1

    connection = health[0]
    assert connection.effective_delta_bytes is None
    assert connection.effective_bitrate_mbps is None
    assert connection.status is HealthStatus.UNKNOWN


@pytest.mark.parametrize(
    ("role", "received", "sent"),
    [
        (SessionRole.PUBLISHER, 1_500_000, 3_467),
        (SessionRole.READER, 3_455, 1_500_000),
    ],
)
def test_rtmp_zero_effective_delta_remains_unknown(
    role: SessionRole,
    received: int,
    sent: int,
) -> None:
    previous = SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=(
            ActiveSession(
                session_id="rtmp-zero-delta-1",
                protocol=SessionProtocol.RTMP,
                role=role,
                state="publish" if role is SessionRole.PUBLISHER else "read",
                remote_ip="127.0.0.1",
                remote_port=58169,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=received,
                bytes_sent=sent,
            ),
        ),
    )

    current = SessionSnapshot(
        captured_at=CAPTURED_AT + timedelta(seconds=10),
        sessions=(
            ActiveSession(
                session_id="rtmp-zero-delta-1",
                protocol=SessionProtocol.RTMP,
                role=role,
                state="publish" if role is SessionRole.PUBLISHER else "read",
                remote_ip="127.0.0.1",
                remote_port=58169,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=received,
                bytes_sent=sent,
            ),
        ),
    )

    health = RTMPConnectionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )

    assert len(health) == 1

    connection = health[0]
    assert connection.effective_delta_bytes is None
    assert connection.effective_bitrate_mbps is None
    assert connection.status is HealthStatus.UNKNOWN


def test_rtmp_path_change_breaks_temporal_identity() -> None:
    previous = SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=(
            ActiveSession(
                session_id="rtmp-reused-id-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.PUBLISHER,
                state="publish",
                remote_ip="127.0.0.1",
                remote_port=58170,
                path="rtmp-old-path",
                connected_since=CAPTURED_AT,
                bytes_received=1_000_000,
                bytes_sent=3_467,
            ),
        ),
    )

    current = SessionSnapshot(
        captured_at=CAPTURED_AT + timedelta(seconds=10),
        sessions=(
            ActiveSession(
                session_id="rtmp-reused-id-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.PUBLISHER,
                state="publish",
                remote_ip="127.0.0.1",
                remote_port=58170,
                path="rtmp-new-path",
                connected_since=CAPTURED_AT,
                bytes_received=2_000_000,
                bytes_sent=3_467,
            ),
        ),
    )

    health = RTMPConnectionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )

    assert len(health) == 1

    connection = health[0]
    assert connection.path_name == "rtmp-new-path"
    assert connection.effective_delta_bytes is None
    assert connection.effective_bitrate_mbps is None
    assert connection.status is HealthStatus.UNKNOWN


def test_rtmp_role_change_breaks_temporal_identity() -> None:
    previous = SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=(
            ActiveSession(
                session_id="rtmp-role-change-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.PUBLISHER,
                state="publish",
                remote_ip="127.0.0.1",
                remote_port=58171,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=1_000_000,
                bytes_sent=100_000,
            ),
        ),
    )

    current = SessionSnapshot(
        captured_at=CAPTURED_AT + timedelta(seconds=10),
        sessions=(
            ActiveSession(
                session_id="rtmp-role-change-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.READER,
                state="read",
                remote_ip="127.0.0.1",
                remote_port=58171,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=1_000_000,
                bytes_sent=500_000,
            ),
        ),
    )

    health = RTMPConnectionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )

    assert len(health) == 1

    connection = health[0]
    assert connection.effective_delta_bytes is None
    assert connection.effective_bitrate_mbps is None
    assert connection.status is HealthStatus.UNKNOWN


def test_rtmp_connected_since_change_breaks_temporal_identity() -> None:
    previous = SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=(
            ActiveSession(
                session_id="rtmp-reconnected-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.PUBLISHER,
                state="publish",
                remote_ip="127.0.0.1",
                remote_port=58172,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=1_000_000,
                bytes_sent=3_467,
            ),
        ),
    )

    current = SessionSnapshot(
        captured_at=CAPTURED_AT + timedelta(seconds=10),
        sessions=(
            ActiveSession(
                session_id="rtmp-reconnected-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.PUBLISHER,
                state="publish",
                remote_ip="127.0.0.1",
                remote_port=58172,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT + timedelta(seconds=5),
                bytes_received=2_000_000,
                bytes_sent=3_467,
            ),
        ),
    )

    health = RTMPConnectionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )

    assert len(health) == 1

    connection = health[0]
    assert connection.effective_delta_bytes is None
    assert connection.effective_bitrate_mbps is None
    assert connection.status is HealthStatus.UNKNOWN


def test_rtmp_previous_non_rtmp_session_breaks_temporal_identity() -> None:
    previous = SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=(
            ActiveSession(
                session_id="protocol-reused-id-1",
                protocol=SessionProtocol.RTSP,
                role=SessionRole.PUBLISHER,
                state="publish",
                remote_ip="127.0.0.1",
                remote_port=58173,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=1_000_000,
                bytes_sent=3_467,
            ),
        ),
    )

    current = SessionSnapshot(
        captured_at=CAPTURED_AT + timedelta(seconds=10),
        sessions=(
            ActiveSession(
                session_id="protocol-reused-id-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.PUBLISHER,
                state="publish",
                remote_ip="127.0.0.1",
                remote_port=58173,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=2_000_000,
                bytes_sent=3_467,
            ),
        ),
    )

    health = RTMPConnectionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )

    assert len(health) == 1

    connection = health[0]
    assert connection.effective_delta_bytes is None
    assert connection.effective_bitrate_mbps is None
    assert connection.status is HealthStatus.UNKNOWN


def test_rtmp_reader_healthy_message_matches_role() -> None:
    previous = SessionSnapshot(
        captured_at=CAPTURED_AT,
        sessions=(
            ActiveSession(
                session_id="rtmp-reader-message-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.READER,
                state="read",
                remote_ip="127.0.0.1",
                remote_port=58174,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=3_455,
                bytes_sent=1_000_000,
            ),
        ),
    )

    current = SessionSnapshot(
        captured_at=CAPTURED_AT + timedelta(seconds=10),
        sessions=(
            ActiveSession(
                session_id="rtmp-reader-message-1",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.READER,
                state="read",
                remote_ip="127.0.0.1",
                remote_port=58174,
                path="rtmp-block8-lab",
                connected_since=CAPTURED_AT,
                bytes_received=3_455,
                bytes_sent=2_000_000,
            ),
        ),
    )

    health = RTMPConnectionHealthService().build(
        previous_snapshot=previous,
        current_snapshot=current,
    )

    assert len(health) == 1

    connection = health[0]
    assert connection.status is HealthStatus.HEALTHY
    assert connection.message == "RTMP reader has observed effective traffic."
