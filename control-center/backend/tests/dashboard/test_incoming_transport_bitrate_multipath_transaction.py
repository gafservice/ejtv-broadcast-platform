"""Functional multipath contracts for application bitrate history."""

from dataclasses import replace
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


def make_path(name, source_id, ready_time):
    return MediaPath(
        name=name,
        configuration_name=name,
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        ready_time=ready_time,
        source=MediaSource(
            source_type="srtConn",
            source_id=source_id,
        ),
    )


def make_snapshot(captured_at, paths):
    return MediaMTXSnapshot(
        captured_at=captured_at,
        paths=tuple(paths),
        reported_item_count=len(paths),
        reported_page_count=1 if paths else 0,
    )


def make_measurement(snapshot, qualities):
    paths = []

    for path in snapshot.paths:
        quality = qualities[path.name]

        available = quality is MeasurementQuality.AVAILABLE

        bitrate = {
            "impact": 6.0,
            "ejtv": 4.0,
            "enlace": 8.0,
        }[path.name]

        paths.append(
            StreamingPathMeasurement(
                name=path.name,
                status=path.status,
                previous_status=path.status,
                reader_count=0,
                reader_delta=0 if available else None,
                inbound_delta_bytes=(
                    int(bitrate * 125_000)
                    if available
                    else None
                ),
                outbound_delta_bytes=0 if available else None,
                inbound_bitrate_bps=(
                    bitrate * 1_000_000
                    if available
                    else None
                ),
                outbound_bitrate_bps=0.0 if available else None,
                state_changed=False,
                quality=quality,
            )
        )

    return StreamingMeasurement(
        captured_at=snapshot.captured_at,
        previous_captured_at=snapshot.captured_at - timedelta(seconds=1),
        interval_seconds=1.0,
        paths=tuple(paths),
        total_inbound_bitrate_bps=sum(
            path.inbound_bitrate_bps
            for path in paths
            if path.quality is MeasurementQuality.AVAILABLE
            and path.inbound_bitrate_bps is not None
        ),
        total_outbound_bitrate_bps=sum(
            path.outbound_bitrate_bps
            for path in paths
            if path.quality is MeasurementQuality.AVAILABLE
            and path.outbound_bitrate_bps is not None
        ),
        quality=MeasurementQuality.AVAILABLE,
    )


def make_application(
    snapshot,
    measurement,
    window,
    snapshot_service,
):
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

    return DashboardApplication(
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


def test_publisher_change_preserves_other_active_paths():
    ready_time = T0 - timedelta(seconds=30)

    previous = make_snapshot(
        T0 - timedelta(seconds=1),
        (
            make_path("impact", "publisher-OLD", ready_time),
            make_path("ejtv", "publisher-EJTV", ready_time),
            make_path("enlace", "publisher-ENLACE", ready_time),
        ),
    )

    current = make_snapshot(
        T0,
        (
            make_path("impact", "publisher-NEW", ready_time),
            make_path("ejtv", "publisher-EJTV", ready_time),
            make_path("enlace", "publisher-ENLACE", ready_time),
        ),
    )

    measurement = make_measurement(
        current,
        {
            "impact": MeasurementQuality.NOT_AVAILABLE,
            "ejtv": MeasurementQuality.AVAILABLE,
            "enlace": MeasurementQuality.AVAILABLE,
        },
    )

    window = IncomingTransportBitrateWindow(window_seconds=60)

    for name, bitrate in (
        ("impact", 3.0),
        ("ejtv", 5.0),
        ("enlace", 7.0),
    ):
        window.observe(
            name,
            observed_at=T0 - timedelta(seconds=5),
            bitrate_mbps=bitrate,
        )

    dashboard_data = Mock(spec=DashboardData)
    dashboard_data.incoming = IncomingPanelData()

    snapshot_service = Mock()
    snapshot_service.build_snapshot.return_value = dashboard_data

    application = make_application(
        current,
        measurement,
        window,
        snapshot_service,
    )

    application._previous_snapshot = previous

    application.build_dashboard()

    committed = application._incoming_transport_bitrate_window

    impact = committed.get("impact", observed_at=T0)
    ejtv = committed.get("ejtv", observed_at=T0)
    enlace = committed.get("enlace", observed_at=T0)

    assert impact.average_mbps is None

    assert ejtv.average_mbps == 4.5
    assert ejtv.minimum_mbps == 4.0
    assert ejtv.maximum_mbps == 5.0

    assert enlace.average_mbps == 7.5
    assert enlace.minimum_mbps == 7.0
    assert enlace.maximum_mbps == 8.0


def test_ready_time_change_resets_only_affected_path():
    previous_ready = T0 - timedelta(seconds=30)
    current_ready = T0 - timedelta(seconds=2)

    previous = make_snapshot(
        T0 - timedelta(seconds=1),
        (
            make_path("impact", "publisher-A", previous_ready),
            make_path("ejtv", "publisher-EJTV", previous_ready),
        ),
    )

    current = make_snapshot(
        T0,
        (
            make_path("impact", "publisher-A", current_ready),
            make_path("ejtv", "publisher-EJTV", previous_ready),
        ),
    )

    measurement = make_measurement(
        current,
        {
            "impact": MeasurementQuality.NOT_AVAILABLE,
            "ejtv": MeasurementQuality.AVAILABLE,
        },
    )

    window = IncomingTransportBitrateWindow(window_seconds=60)

    window.observe(
        "impact",
        observed_at=T0 - timedelta(seconds=5),
        bitrate_mbps=3.0,
    )

    window.observe(
        "ejtv",
        observed_at=T0 - timedelta(seconds=5),
        bitrate_mbps=5.0,
    )

    dashboard_data = Mock(spec=DashboardData)
    dashboard_data.incoming = IncomingPanelData()

    snapshot_service = Mock()
    snapshot_service.build_snapshot.return_value = dashboard_data

    application = make_application(
        current,
        measurement,
        window,
        snapshot_service,
    )

    application._previous_snapshot = previous

    application.build_dashboard()

    committed = application._incoming_transport_bitrate_window

    assert committed.get(
        "impact",
        observed_at=T0,
    ).average_mbps is None

    assert committed.get(
        "ejtv",
        observed_at=T0,
    ).average_mbps == 4.5


def test_failure_after_snapshot_build_does_not_commit_window():
    ready_time = T0 - timedelta(seconds=30)

    current = make_snapshot(
        T0,
        (make_path("impact", "publisher-A", ready_time),),
    )

    measurement = make_measurement(
        current,
        {"impact": MeasurementQuality.AVAILABLE},
    )

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
        current,
        measurement,
        window,
        snapshot_service,
    )

    application.reconcile_incoming_selection = Mock(
        side_effect=RuntimeError("controlled late failure")
    )

    with pytest.raises(
        RuntimeError,
        match="controlled late failure",
    ):
        application.build_dashboard()

    assert application._incoming_transport_bitrate_window.get(
        "impact",
        observed_at=T0,
    ).average_mbps == 4.0

    assert application._previous_snapshot is None
