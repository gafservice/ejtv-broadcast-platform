"""End-to-end contracts for INCOMING transport bitrate projection."""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.dashboard.services.dashboard_snapshot_service import (
    DashboardSnapshotInput,
    DashboardSnapshotService,
)
from app.dashboard.services.incoming_transport_bitrate_window import (
    IncomingTransportBitrateStatistics,
)
from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaSource,
    StreamingMeasurement,
    StreamingPathMeasurement,
)


@pytest.fixture
def incoming_capture():
    captured_at = datetime(
        2026, 10, 19, 18, 0, tzinfo=timezone.utc
    )

    expected = {
        "impact": (6.0, 5.8, 5.5, 6.2),
        "ejtv": (4.0, 4.1, 3.9, 4.3),
        "enlace": (8.0, 7.9, 7.6, 8.2),
    }

    paths = tuple(
        MediaPath(
            name=name,
            configuration_name=name,
            status=MediaPathStatus.ACTIVE,
            ready=True,
            available=True,
            online=True,
            source=MediaSource(
                source_type="srt",
                source_id=name,
            ),
        )
        for name in expected
    )

    snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=paths,
        reported_item_count=len(paths),
        reported_page_count=1,
    )

    measurements = tuple(
        StreamingPathMeasurement(
            name=name,
            status=MediaPathStatus.ACTIVE,
            previous_status=MediaPathStatus.ACTIVE,
            reader_count=0,
            reader_delta=0,
            inbound_delta_bytes=0,
            outbound_delta_bytes=0,
            inbound_bitrate_bps=values[0] * 1_000_000,
            outbound_bitrate_bps=0.0,
            state_changed=False,
            quality=MeasurementQuality.AVAILABLE,
        )
        for name, values in expected.items()
    )

    measurement = StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=datetime(
            2026, 10, 19, 17, 59, 59,
            tzinfo=timezone.utc,
        ),
        interval_seconds=1.0,
        paths=measurements,
        total_inbound_bitrate_bps=18_000_000.0,
        total_outbound_bitrate_bps=0.0,
        quality=MeasurementQuality.AVAILABLE,
    )

    session_snapshot = Mock()
    session_snapshot.sessions = ()

    statistics = {
        name: IncomingTransportBitrateStatistics(
            average_mbps=values[1],
            minimum_mbps=values[2],
            maximum_mbps=values[3],
        )
        for name, values in expected.items()
    }

    return (
        snapshot,
        measurement,
        session_snapshot,
        statistics,
        expected,
    )


def build_dashboard(capture, statistics):
    snapshot, measurement, session_snapshot, _, _ = capture

    return DashboardSnapshotService().build_snapshot(
        DashboardSnapshotInput(
            hostname="ejtv-test",
            mediamtx_online=True,
            api_online=True,
            snapshot=snapshot,
            measurement=measurement,
            session_snapshot=session_snapshot,
            incoming_transport_bitrate_statistics=statistics,
        )
    )


def test_statistics_reach_all_incoming_rows(incoming_capture):
    """Each path retains its own instant/AVG/MIN/MAX values."""

    dashboard = build_dashboard(
        incoming_capture,
        incoming_capture[3],
    )

    assert dashboard.incoming is not None

    rows = {
        row.path_name: row
        for row in dashboard.incoming.rows
    }

    expected = incoming_capture[4]

    assert set(rows) == set(expected)

    for name, values in expected.items():
        row = rows[name]

        assert row.bitrate_receive_mbps == values[0]
        assert row.bitrate_average_mbps == values[1]
        assert row.bitrate_minimum_mbps == values[2]
        assert row.bitrate_maximum_mbps == values[3]


def test_missing_statistics_preserve_instantaneous_bitrate(
    incoming_capture,
):
    """Without history, instant bitrate remains available."""

    dashboard = build_dashboard(
        incoming_capture,
        None,
    )

    assert dashboard.incoming is not None

    rows = {
        row.path_name: row
        for row in dashboard.incoming.rows
    }

    expected = incoming_capture[4]

    assert set(rows) == set(expected)

    for name, values in expected.items():
        row = rows[name]

        assert row.bitrate_receive_mbps == values[0]
        assert row.bitrate_average_mbps is None
        assert row.bitrate_minimum_mbps is None
        assert row.bitrate_maximum_mbps is None
