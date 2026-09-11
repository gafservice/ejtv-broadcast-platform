from datetime import UTC, datetime, timedelta

import pytest

from app.domain.streaming import HealthStatus, RTMPConnectionHealth
from app.services.rtmp_connection_health_window import (
    RTMPConnectionHealthWindow,
)


OBSERVED_AT = datetime(2026, 9, 10, 15, 0, 0, tzinfo=UTC)


def make_health(
    status: HealthStatus,
    *,
    connection_id: str = "rtmp-reader-1",
    bitrate: float | None = None,
) -> RTMPConnectionHealth:
    return RTMPConnectionHealth(
        connection_id=connection_id,
        path_name="impact",
        state="read",
        effective_delta_bytes=(
            1_000_000 if bitrate is not None else None
        ),
        effective_bitrate_mbps=bitrate,
        outbound_frames_discarded=None,
        status=status,
        message=f"RTMP {status.value}",
    )


def test_first_unknown_remains_unknown() -> None:
    window = RTMPConnectionHealthWindow(window_seconds=5)

    result = window.stabilize(
        make_health(HealthStatus.UNKNOWN),
        observed_at=OBSERVED_AT,
    )

    assert result.status is HealthStatus.UNKNOWN


def test_healthy_is_committed_immediately() -> None:
    window = RTMPConnectionHealthWindow(window_seconds=5)

    result = window.stabilize(
        make_health(HealthStatus.HEALTHY, bitrate=5.0),
        observed_at=OBSERVED_AT,
    )

    assert result.status is HealthStatus.HEALTHY
    assert result.effective_bitrate_mbps == 5.0


def test_brief_unknown_preserves_healthy_status_only() -> None:
    window = RTMPConnectionHealthWindow(window_seconds=5)

    window.stabilize(
        make_health(HealthStatus.HEALTHY, bitrate=5.0),
        observed_at=OBSERVED_AT,
    )

    result = window.stabilize(
        make_health(HealthStatus.UNKNOWN),
        observed_at=OBSERVED_AT + timedelta(seconds=2),
    )

    assert result.status is HealthStatus.HEALTHY
    assert result.effective_delta_bytes is None
    assert result.effective_bitrate_mbps is None


def test_unknown_after_window_expires() -> None:
    window = RTMPConnectionHealthWindow(window_seconds=5)

    window.stabilize(
        make_health(HealthStatus.HEALTHY, bitrate=5.0),
        observed_at=OBSERVED_AT,
    )

    result = window.stabilize(
        make_health(HealthStatus.UNKNOWN),
        observed_at=OBSERVED_AT + timedelta(seconds=5),
    )

    assert result.status is HealthStatus.UNKNOWN


def test_new_healthy_refreshes_window() -> None:
    window = RTMPConnectionHealthWindow(window_seconds=5)

    window.stabilize(
        make_health(HealthStatus.HEALTHY, bitrate=5.0),
        observed_at=OBSERVED_AT,
    )
    window.stabilize(
        make_health(HealthStatus.HEALTHY, bitrate=4.8),
        observed_at=OBSERVED_AT + timedelta(seconds=4),
    )

    result = window.stabilize(
        make_health(HealthStatus.UNKNOWN),
        observed_at=OBSERVED_AT + timedelta(seconds=7),
    )

    assert result.status is HealthStatus.HEALTHY


def test_connections_are_independent() -> None:
    window = RTMPConnectionHealthWindow(window_seconds=5)

    window.stabilize(
        make_health(
            HealthStatus.HEALTHY,
            connection_id="rtmp-a",
            bitrate=5.0,
        ),
        observed_at=OBSERVED_AT,
    )

    result = window.stabilize(
        make_health(
            HealthStatus.UNKNOWN,
            connection_id="rtmp-b",
        ),
        observed_at=OBSERVED_AT + timedelta(seconds=1),
    )

    assert result.status is HealthStatus.UNKNOWN


def test_out_of_order_observation_is_rejected() -> None:
    window = RTMPConnectionHealthWindow(window_seconds=5)

    window.stabilize(
        make_health(HealthStatus.HEALTHY, bitrate=5.0),
        observed_at=OBSERVED_AT,
    )

    with pytest.raises(ValueError):
        window.stabilize(
            make_health(HealthStatus.UNKNOWN),
            observed_at=OBSERVED_AT - timedelta(seconds=1),
        )
