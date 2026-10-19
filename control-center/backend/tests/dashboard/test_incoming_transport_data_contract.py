"""Contract tests for incoming transport presentation evidence."""

from datetime import UTC, datetime

from app.dashboard.models.incoming_panel import IncomingRowData
from app.domain.streaming.health import HealthStatus


def _row() -> IncomingRowData:
    return IncomingRowData(
        path_name="impact",
        source="SRT",
        status="ACTIVE",
        bitrate_receive_mbps=5.0,
        health_status=HealthStatus.HEALTHY,
        transport_health_status=HealthStatus.HEALTHY,
    )


def test_incoming_row_exposes_path_transport_evidence() -> None:
    row = _row()

    assert row.transport_source_type is None
    assert row.transport_ready is None
    assert row.transport_available is None
    assert row.transport_online is None
    assert row.transport_available_since is None
    assert row.transport_online_since is None
    assert row.transport_received_bytes is None
    assert row.transport_inbound_frames_in_error is None


def test_incoming_row_exposes_canonical_transport_timestamps() -> None:
    row = _row()

    assert row.transport_observed_at is None
    assert row.transport_health_since is None


def test_incoming_row_accepts_real_transport_evidence() -> None:
    observed_at = datetime(2026, 10, 19, 15, 0, tzinfo=UTC)
    available_since = datetime(2026, 10, 18, 18, 0, tzinfo=UTC)

    row = IncomingRowData(
        path_name="impact",
        source="SRT",
        status="ACTIVE",
        bitrate_receive_mbps=5.0,
        health_status=HealthStatus.HEALTHY,
        transport_health_status=HealthStatus.HEALTHY,
        transport_source_type="srtSource",
        transport_ready=True,
        transport_available=True,
        transport_online=True,
        transport_available_since=available_since,
        transport_online_since=available_since,
        transport_received_bytes=58_566_181_475,
        transport_inbound_frames_in_error=0,
        transport_observed_at=observed_at,
        transport_health_since=observed_at,
    )

    assert row.transport_source_type == "srtSource"
    assert row.transport_ready is True
    assert row.transport_received_bytes == 58_566_181_475
    assert row.transport_inbound_frames_in_error == 0
    assert row.transport_observed_at == observed_at
