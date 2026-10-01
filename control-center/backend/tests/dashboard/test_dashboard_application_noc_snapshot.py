"""Contract test for canonical NOC snapshot dashboard integration.

ENG-013C — Terminal Dashboard

The dashboard already captures SystemResources and NetworkInterfaceInfo.
The NOC projection must consume that same capture.  It must not perform
a second system capture merely to populate canonical NodeMetric state.

This RED test defines only the application boundary.  It does not define
presentation layout or duplicate NOC domain models.
"""

from __future__ import annotations

import inspect

from app.dashboard.application import DashboardApplication


def test_dashboard_application_accepts_canonical_noc_snapshot_projection() -> None:
    """DashboardApplication must expose a NOC snapshot collaborator."""

    signature = inspect.signature(
        DashboardApplication.__init__
    )

    assert "noc_snapshot_projection" in signature.parameters


def test_noc_snapshot_projection_receives_existing_system_capture() -> None:
    """The projection boundary must support reuse of the existing capture."""

    module = __import__(
        "app.dashboard.application",
        fromlist=["NocSnapshotProjection"],
    )

    projection_type = getattr(
        module,
        "NocSnapshotProjection",
        None,
    )

    assert projection_type is not None

    process = getattr(
        projection_type,
        "project_from_capture",
        None,
    )

    assert process is not None

    signature = inspect.signature(process)

    assert "resources" in signature.parameters
    assert "interface_infos" in signature.parameters


def test_noc_snapshot_projection_reuses_existing_capture() -> None:
    """Projection must reuse one existing capture and return its snapshot."""

    from datetime import datetime, timezone
    from unittest.mock import Mock

    from app.dashboard.application import NocSnapshotProjection

    captured_at = datetime(
        2026,
        9,
        30,
        23,
        30,
        tzinfo=timezone.utc,
    )

    resources = Mock()
    resources.captured_at = captured_at

    interface_infos = (
        Mock(name="interface-1"),
        Mock(name="interface-2"),
    )

    node_id = Mock(name="node-id")
    instance_id = Mock(name="instance-id")

    telemetry_refresh_service = Mock()
    snapshot_service = Mock()

    expected_snapshot = Mock(name="node-snapshot")

    snapshot_service.build.return_value = (
        expected_snapshot
    )

    projection = NocSnapshotProjection(
        telemetry_refresh_service=(
            telemetry_refresh_service
        ),
        snapshot_service=snapshot_service,
        node_id=node_id,
        instance_id=instance_id,
    )

    actual_snapshot = projection.project_from_capture(
        resources=resources,
        interface_infos=interface_infos,
    )

    telemetry_refresh_service.refresh_from_capture.assert_called_once_with(
        node_id=node_id,
        instance_id=instance_id,
        resources=resources,
        interface_infos=interface_infos,
    )

    snapshot_service.build.assert_called_once_with(
        node_id,
        instance_id,
        timestamp=captured_at,
    )

    assert actual_snapshot is expected_snapshot


def test_build_dashboard_projects_same_system_capture_into_noc() -> None:
    """Dashboard must project the exact capture it already owns."""

    from unittest.mock import Mock


    snapshot = Mock()
    snapshot.captured_at = Mock()

    session_snapshot = Mock()

    mediamtx_adapter = Mock()
    mediamtx_adapter.health.return_value = True
    mediamtx_adapter.get_snapshot.return_value = snapshot

    session_adapter = Mock()
    session_adapter.get_snapshot.return_value = (
        session_snapshot
    )

    streaming_service = Mock()
    streaming_service.compare.return_value = Mock()

    session_service = Mock()
    session_service.measure.return_value = Mock()

    system_service = Mock()

    system_info = Mock()
    system_info.hostname = "ejtv-01"

    system_resources = Mock(
        name="system-resources"
    )

    interface_infos = Mock(
        name="interface-infos"
    )

    system_service.get_system_info.return_value = (
        system_info
    )

    system_service.get_system_resources.return_value = (
        system_resources
    )

    system_service.get_network_interface_infos.return_value = (
        interface_infos
    )

    network_telemetry_service = Mock()
    network_telemetry_service.build.return_value = Mock()

    dashboard_service = Mock()
    dashboard_service.build_network_interfaces_panel.return_value = (
        Mock()
    )

    dashboard_data = Mock(name="dashboard-data")

    dashboard_data.active_connections = Mock()
    dashboard_data.active_connections.total_items = 0

    dashboard_data.active_alarms = None
    dashboard_data.recent_events = None

    dashboard_snapshot_service = Mock()
    dashboard_snapshot_service.build_snapshot.return_value = (
        dashboard_data
    )

    noc_snapshot_projection = Mock()
    noc_snapshot_projection.project_from_capture.return_value = (
        Mock(name="noc-snapshot")
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

    system_service.get_system_resources.assert_called_once_with()

    system_service.get_network_interface_infos.assert_called_once_with()

    network_telemetry_service.build.assert_called_once_with(
        previous=None,
        current=system_resources,
        interface_infos=interface_infos,
    )

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

    assert snapshot_input.system_resources is system_resources
