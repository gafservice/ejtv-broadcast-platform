"""Contract for canonical NodeSnapshot presentation transport.

ENG-013C — Terminal Dashboard
Block 234E — NodeSnapshot -> Presentation Boundary

This contract defines transport only:

NocSnapshotProjection
    -> DashboardApplication
    -> DashboardSnapshotInput
    -> DashboardSnapshotService
    -> DashboardData

It does not define rendering or replace SystemResources.
"""

from __future__ import annotations

from dataclasses import fields
from unittest.mock import Mock

from app.dashboard.application import DashboardApplication
from app.dashboard.models.dashboard_models import DashboardData
from app.dashboard.services.dashboard_snapshot_service import (
    DashboardSnapshotInput,
)


def _field_names(dataclass_type: type) -> set[str]:
    return {field.name for field in fields(dataclass_type)}


def test_dashboard_snapshot_input_accepts_canonical_noc_snapshot() -> None:
    assert "noc_snapshot" in _field_names(DashboardSnapshotInput)


def test_dashboard_data_preserves_canonical_noc_snapshot() -> None:
    assert "noc_snapshot" in _field_names(DashboardData)


def test_snapshot_service_preserves_same_noc_snapshot_instance() -> None:
    from datetime import UTC, datetime

    from app.dashboard.services.dashboard_snapshot_service import (
        DashboardSnapshotService,
    )
    from app.domain.streaming import (
        MeasurementQuality,
        MediaMTXSnapshot,
        StreamingMeasurement,
    )

    captured_at = datetime(
        2026,
        10,
        2,
        9,
        30,
        tzinfo=UTC,
    )

    media_snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    measurement = StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=None,
        interval_seconds=None,
        paths=(),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    expected_noc_snapshot = Mock(
        name="canonical-node-snapshot"
    )
    expected_noc_snapshot.capacity = None

    result = DashboardSnapshotService().build_snapshot(
        DashboardSnapshotInput(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot=media_snapshot,
            measurement=measurement,
            noc_snapshot=expected_noc_snapshot,
        )
    )

    assert result.noc_snapshot is expected_noc_snapshot


def test_dashboard_application_transports_projected_noc_snapshot() -> None:
    snapshot = Mock()
    snapshot.captured_at = Mock()

    session_snapshot = Mock()

    mediamtx_adapter = Mock()
    mediamtx_adapter.health.return_value = True
    mediamtx_adapter.get_snapshot.return_value = snapshot

    session_adapter = Mock()
    session_adapter.get_snapshot.return_value = session_snapshot

    streaming_service = Mock()
    streaming_service.compare.return_value = Mock()

    session_service = Mock()
    session_service.measure.return_value = Mock()

    system_service = Mock()

    system_info = Mock()
    system_info.hostname = "ejtv-01"

    system_resources = Mock(name="system-resources")
    interface_infos = Mock(name="interface-infos")

    system_service.get_system_info.return_value = system_info
    system_service.get_system_resources.return_value = system_resources
    system_service.get_network_interface_infos.return_value = interface_infos

    network_telemetry_service = Mock()
    network_telemetry_service.build.return_value = Mock()

    dashboard_service = Mock()
    dashboard_service.build_network_interfaces_panel.return_value = Mock()

    dashboard_data = Mock(name="dashboard-data")
    dashboard_data.active_connections = Mock()
    dashboard_data.active_connections.total_items = 0
    dashboard_data.active_alarms = None
    dashboard_data.recent_events = None

    dashboard_snapshot_service = Mock()
    dashboard_snapshot_service.build_snapshot.return_value = dashboard_data

    expected_noc_snapshot = Mock(name="canonical-node-snapshot")

    noc_snapshot_projection = Mock()
    noc_snapshot_projection.project_from_capture.return_value = (
        expected_noc_snapshot
    )

    application = DashboardApplication(
        noc_snapshot_projection=noc_snapshot_projection,
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        session_service=session_service,
        dashboard_service=dashboard_service,
        dashboard_renderer=Mock(),
        system_service=system_service,
        dashboard_snapshot_service=dashboard_snapshot_service,
        network_telemetry_service=network_telemetry_service,
    )

    result = application.build_dashboard()

    assert result is dashboard_data

    noc_snapshot_projection.project_from_capture.assert_called_once_with(
        resources=system_resources,
        interface_infos=interface_infos,
    )

    snapshot_input = (
        dashboard_snapshot_service
        .build_snapshot
        .call_args
        .args[0]
    )

    assert snapshot_input.noc_snapshot is expected_noc_snapshot
