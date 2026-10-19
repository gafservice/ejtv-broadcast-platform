"""RED contracts for INCOMING transport bitrate runtime integration."""

from dataclasses import fields
from inspect import signature

from app.dashboard.application import DashboardApplication
from app.dashboard.models.incoming_panel import IncomingRowData
from app.dashboard.services.dashboard_snapshot_service import (
    DashboardSnapshotInput,
)
from app.dashboard.services.incoming_transport_bitrate_window import (
    IncomingTransportBitrateWindow,
)


def test_application_accepts_persistent_incoming_bitrate_window():
    """Application must support explicit injection of its rolling window."""

    parameters = signature(DashboardApplication.__init__).parameters

    assert "incoming_transport_bitrate_window" in parameters

    assert IncomingTransportBitrateWindow is not None


def test_dashboard_snapshot_input_transports_bitrate_statistics():
    """The snapshot contract must carry per-path temporal statistics."""

    field_names = {
        field.name
        for field in fields(DashboardSnapshotInput)
    }

    assert "incoming_transport_bitrate_statistics" in field_names


def test_incoming_row_exposes_bitrate_average_minimum_maximum():
    """The presentation model must expose statistics independently."""

    field_names = {
        field.name
        for field in fields(IncomingRowData)
    }

    expected = {
        "bitrate_average_mbps",
        "bitrate_minimum_mbps",
        "bitrate_maximum_mbps",
    }

    assert expected <= field_names


def test_incoming_projection_transports_independent_bitrate_statistics():
    """Per-path statistics must reach the presentation rows unchanged."""

    from datetime import datetime, timezone

    from app.dashboard.services.dashboard_service import DashboardService
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

    captured_at = datetime(2026, 10, 19, 18, 0, tzinfo=timezone.utc)

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
            source=MediaSource(source_type="srt", source_id=name),
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
            2026, 10, 19, 17, 59, 59, tzinfo=timezone.utc
        ),
        interval_seconds=1.0,
        paths=measurements,
        total_inbound_bitrate_bps=18_000_000.0,
        total_outbound_bitrate_bps=0.0,
        quality=MeasurementQuality.AVAILABLE,
    )

    statistics = {
        name: IncomingTransportBitrateStatistics(
            average_mbps=values[1],
            minimum_mbps=values[2],
            maximum_mbps=values[3],
        )
        for name, values in expected.items()
    }

    from unittest.mock import Mock

    session_snapshot = Mock()
    session_snapshot.sessions = ()

    panel = DashboardService().build_incoming_panel(
        snapshot=snapshot,
        measurement=measurement,
        session_snapshot=session_snapshot,
        health=None,
        incoming_transport_bitrate_statistics=statistics,
    )

    rows = {row.path_name: row for row in panel.rows}

    assert set(rows) == set(expected)

    for name, values in expected.items():
        row = rows[name]

        assert row.bitrate_receive_mbps == values[0]
        assert row.bitrate_average_mbps == values[1]
        assert row.bitrate_minimum_mbps == values[2]
        assert row.bitrate_maximum_mbps == values[3]
