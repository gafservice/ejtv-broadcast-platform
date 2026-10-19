"""Functional transaction contracts for application bitrate history."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from app.dashboard.application import DashboardApplication
from app.dashboard.models import DashboardData
from app.dashboard.models.incoming_panel import IncomingPanelData
from app.dashboard.services.incoming_transport_bitrate_window import (
    IncomingTransportBitrateWindow,
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


T0 = datetime(2026, 10, 19, 18, 0, tzinfo=UTC)


def make_capture():
    path = MediaPath(
        name="impact",
        configuration_name="impact",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(
            source_type="srtConn",
            source_id="publisher-A",
        ),
    )

    snapshot = MediaMTXSnapshot(
        captured_at=T0,
        paths=(path,),
        reported_item_count=1,
        reported_page_count=1,
    )

    measurement_path = StreamingPathMeasurement(
        name="impact",
        status=MediaPathStatus.ACTIVE,
        previous_status=MediaPathStatus.ACTIVE,
        reader_count=0,
        reader_delta=0,
        inbound_delta_bytes=750_000,
        outbound_delta_bytes=0,
        inbound_bitrate_bps=6_000_000.0,
        outbound_bitrate_bps=0.0,
        state_changed=False,
        quality=MeasurementQuality.AVAILABLE,
    )

    measurement = StreamingMeasurement(
        captured_at=T0,
        previous_captured_at=T0 - timedelta(seconds=1),
        interval_seconds=1.0,
        paths=(measurement_path,),
        total_inbound_bitrate_bps=6_000_000.0,
        total_outbound_bitrate_bps=0.0,
        quality=MeasurementQuality.AVAILABLE,
    )

    return snapshot, measurement


def make_application(
    *,
    window,
    snapshot_service,
):
    snapshot, measurement = make_capture()

    mediamtx_adapter = Mock()
    mediamtx_adapter.health.return_value = True
    mediamtx_adapter.get_snapshot.return_value = snapshot
    mediamtx_adapter.get_source_configurations.return_value = {}

    session_snapshot = Mock()
    session_snapshot.sessions = ()

    session_adapter = Mock()
    session_adapter.get_snapshot.return_value = session_snapshot

    streaming_service = Mock()
    streaming_service.compare.return_value = measurement

    session_service = Mock()
    session_service.measure.return_value = Mock()

    dashboard_service = Mock()
    dashboard_service.build_network_interfaces_panel.return_value = Mock()

    dashboard_renderer = Mock()

    system_service = Mock()
    system_service.get_system_info.return_value = Mock(
        hostname="ejtv-test"
    )
    system_service.get_system_resources.return_value = Mock()
    system_service.get_network_interface_infos.return_value = ()

    network_telemetry_service = Mock()
    network_telemetry_service.build.return_value = Mock()

    application = DashboardApplication(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        session_service=session_service,
        dashboard_service=dashboard_service,
        dashboard_renderer=dashboard_renderer,
        system_service=system_service,
        network_telemetry_service=network_telemetry_service,
        dashboard_snapshot_service=snapshot_service,
        incoming_transport_bitrate_window=window,
    )

    return application


def test_valid_measurement_is_forwarded_and_committed():
    window = IncomingTransportBitrateWindow(window_seconds=60)

    dashboard_data = Mock(spec=DashboardData)
    dashboard_data.incoming = IncomingPanelData()

    snapshot_service = Mock()
    snapshot_service.build_snapshot.return_value = dashboard_data

    application = make_application(
        window=window,
        snapshot_service=snapshot_service,
    )

    application.build_dashboard()

    snapshot_service.build_snapshot.assert_called_once()

    snapshot_input = snapshot_service.build_snapshot.call_args.args[0]

    statistics = snapshot_input.incoming_transport_bitrate_statistics

    assert statistics is not None
    assert statistics["impact"].average_mbps == 6.0
    assert statistics["impact"].minimum_mbps == 6.0
    assert statistics["impact"].maximum_mbps == 6.0

    committed = application._incoming_transport_bitrate_window

    assert committed.get(
        "impact",
        observed_at=T0,
    ).average_mbps == 6.0


def test_failed_snapshot_build_preserves_persistent_history():
    window = IncomingTransportBitrateWindow(window_seconds=60)

    window.observe(
        "impact",
        observed_at=T0 - timedelta(seconds=5),
        bitrate_mbps=4.0,
    )

    snapshot_service = Mock()
    snapshot_service.build_snapshot.side_effect = RuntimeError(
        "controlled snapshot failure"
    )

    application = make_application(
        window=window,
        snapshot_service=snapshot_service,
    )

    with pytest.raises(
        RuntimeError,
        match="controlled snapshot failure",
    ):
        application.build_dashboard()

    assert window.get(
        "impact",
        observed_at=T0,
    ).average_mbps == 4.0

    assert application._previous_snapshot is None


def test_existing_history_is_combined_with_valid_measurement():
    """The runtime must combine historical and current valid samples."""

    window = IncomingTransportBitrateWindow(window_seconds=60)

    window.observe(
        "impact",
        observed_at=T0 - timedelta(seconds=5),
        bitrate_mbps=4.0,
    )

    dashboard_data = Mock(spec=DashboardData)
    dashboard_data.incoming = IncomingPanelData()

    snapshot_service = Mock()
    snapshot_service.build_snapshot.return_value = dashboard_data

    application = make_application(
        window=window,
        snapshot_service=snapshot_service,
    )

    application.build_dashboard()

    snapshot_input = snapshot_service.build_snapshot.call_args.args[0]
    statistics = snapshot_input.incoming_transport_bitrate_statistics

    assert statistics is not None

    impact = statistics["impact"]

    assert impact.average_mbps == 5.0
    assert impact.minimum_mbps == 4.0
    assert impact.maximum_mbps == 6.0

    committed = application._incoming_transport_bitrate_window

    result = committed.get("impact", observed_at=T0)

    assert result.average_mbps == 5.0
    assert result.minimum_mbps == 4.0
    assert result.maximum_mbps == 6.0


def test_changed_source_resets_only_affected_path():
    """Publisher replacement must not discard another path's history."""

    from dataclasses import replace

    window = IncomingTransportBitrateWindow(window_seconds=60)

    window.observe(
        "impact",
        observed_at=T0 - timedelta(seconds=5),
        bitrate_mbps=4.0,
    )

    window.observe(
        "ejtv",
        observed_at=T0 - timedelta(seconds=5),
        bitrate_mbps=8.0,
    )

    dashboard_data = Mock(spec=DashboardData)
    dashboard_data.incoming = IncomingPanelData()

    snapshot_service = Mock()
    snapshot_service.build_snapshot.return_value = dashboard_data

    application = make_application(
        window=window,
        snapshot_service=snapshot_service,
    )

    current_snapshot, measurement = make_capture()

    previous_path = replace(
        current_snapshot.paths[0],
        source=MediaSource(
            source_type="srtConn",
            source_id="publisher-OLD",
        ),
    )

    previous_snapshot = replace(
        current_snapshot,
        captured_at=T0 - timedelta(seconds=1),
        paths=(previous_path,),
    )

    application._previous_snapshot = previous_snapshot

    # The measurement represents a new publisher's first capture.
    unavailable_path = replace(
        measurement.paths[0],
        inbound_delta_bytes=None,
        outbound_delta_bytes=None,
        inbound_bitrate_bps=None,
        outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    unavailable_measurement = replace(
        measurement,
        paths=(unavailable_path,),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    application._streaming_service.compare.return_value = (
        unavailable_measurement
    )

    application.build_dashboard()

    committed = application._incoming_transport_bitrate_window

    impact = committed.get("impact", observed_at=T0)

    assert impact.average_mbps is None
    assert impact.minimum_mbps is None
    assert impact.maximum_mbps is None

    # EJTV is absent from the current valid inventory.
    # Reconciliation must retire its historical samples.
    ejtv = committed.get("ejtv", observed_at=T0)

    assert ejtv.average_mbps is None
