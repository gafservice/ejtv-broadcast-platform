"""Capacity lifecycle contract for Terminal Dashboard.

ENG-013C — Terminal Dashboard

Capacity belongs to canonical NOC state, but it must not be refreshed by
NocSnapshotProjection on every dashboard cycle.

The dashboard already owns one SystemResources capture per cycle.  Capacity
initialization must reuse that capture, publish canonical NodeCapacity once,
and then leave subsequent capacity lifecycle decisions outside the snapshot
projection.

No second SystemResources capture is allowed.
"""

from __future__ import annotations

import inspect
from unittest.mock import Mock

import pytest

from app.dashboard.application import (
    DashboardApplication,
    NocSnapshotProjection,
)


def test_dashboard_application_accepts_capacity_initializer():
    """DashboardApplication must expose a Capacity lifecycle collaborator."""

    signature = inspect.signature(
        DashboardApplication.__init__
    )

    assert "noc_capacity_initializer" in signature.parameters


def test_capacity_initializer_uses_existing_capture_once():
    """
    Capacity initialization must receive the dashboard's existing capture.

    The initializer is invoked once even when multiple dashboards are built.
    It must not own or trigger SystemService capture itself.
    """

    from app.dashboard.application import (
        NocCapacityInitializer,
    )

    resources_1 = Mock(name="resources-1")
    resources_2 = Mock(name="resources-2")

    node_id = Mock(name="node-id")
    instance_id = Mock(name="instance-id")

    capacity = Mock(name="capacity")

    capacity_provider = Mock(
        name="capacity-provider"
    )
    capacity_service = Mock(
        name="capacity-service"
    )

    capacity_provider.collect.return_value = (
        capacity
    )

    initializer = NocCapacityInitializer(
        capacity_provider=capacity_provider,
        capacity_service=capacity_service,
        node_id=node_id,
        instance_id=instance_id,
    )

    initializer.initialize_from_capture(
        resources=resources_1
    )

    initializer.initialize_from_capture(
        resources=resources_2
    )

    capacity_provider.collect.assert_called_once_with(
        resources_1
    )

    capacity_service.publish.assert_called_once_with(
        node_id=node_id,
        instance_id=instance_id,
        capacity=capacity,
    )

    assert not hasattr(
        initializer,
        "_system_service",
    )

    assert not hasattr(
        initializer,
        "get_system_resources",
    )


def test_capacity_initializer_marks_initialized_only_after_publish():
    """
    A failed first publication must remain retryable.

    Initialization is complete only after canonical CapacityService.publish()
    succeeds.
    """

    from app.dashboard.application import (
        NocCapacityInitializer,
    )

    resources = Mock(name="resources")
    node_id = Mock(name="node-id")
    instance_id = Mock(name="instance-id")
    capacity = Mock(name="capacity")

    capacity_provider = Mock()
    capacity_provider.collect.return_value = (
        capacity
    )

    capacity_service = Mock()

    capacity_service.publish.side_effect = [
        RuntimeError("capacity publish failed"),
        capacity,
    ]

    initializer = NocCapacityInitializer(
        capacity_provider=capacity_provider,
        capacity_service=capacity_service,
        node_id=node_id,
        instance_id=instance_id,
    )

    with pytest.raises(
        RuntimeError,
        match="capacity publish failed",
    ):
        initializer.initialize_from_capture(
            resources=resources
        )

    initializer.initialize_from_capture(
        resources=resources
    )

    assert capacity_provider.collect.call_count == 2
    assert capacity_service.publish.call_count == 2


def test_noc_snapshot_projection_has_no_capacity_dependencies():
    """
    Snapshot projection must consume already-initialized canonical NOC state.

    Capacity collection/publication is not part of per-cycle projection.
    """

    signature = inspect.signature(
        NocSnapshotProjection.__init__
    )

    assert "capacity_provider" not in signature.parameters
    assert "capacity_service" not in signature.parameters

    projection = NocSnapshotProjection(
        telemetry_refresh_service=Mock(),
        snapshot_service=Mock(),
        node_id=Mock(),
        instance_id=Mock(),
    )

    assert not hasattr(
        projection,
        "_capacity_provider",
    )

    assert not hasattr(
        projection,
        "_capacity_service",
    )


def test_dashboard_reuses_same_capture_for_capacity_and_projection():
    """
    One SystemResources capture must feed both one-shot Capacity initialization
    and canonical telemetry/snapshot projection.
    """

    snapshot = Mock()
    snapshot.captured_at = Mock()

    session_snapshot = Mock()

    mediamtx_adapter = Mock()
    mediamtx_adapter.health.return_value = True
    mediamtx_adapter.get_snapshot.return_value = (
        snapshot
    )

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

    capacity_initializer = Mock(
        name="capacity-initializer"
    )

    noc_snapshot_projection = Mock(
        name="noc-snapshot-projection"
    )

    network_telemetry_service = Mock()
    network_telemetry_service.build.return_value = (
        Mock()
    )

    dashboard_service = Mock()
    dashboard_service.build_network_interfaces_panel.return_value = (
        Mock()
    )

    dashboard_data = Mock(
        name="dashboard-data"
    )

    dashboard_data.active_connections = Mock()
    dashboard_data.active_connections.total_items = 0

    dashboard_data.active_alarms = None
    dashboard_data.recent_events = None

    dashboard_snapshot_service = Mock()
    dashboard_snapshot_service.build_snapshot.return_value = (
        dashboard_data
    )

    application = DashboardApplication(
        noc_capacity_initializer=capacity_initializer,
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

    capacity_initializer.initialize_from_capture.assert_called_once_with(
        resources=system_resources
    )

    noc_snapshot_projection.project_from_capture.assert_called_once_with(
        resources=system_resources,
        interface_infos=interface_infos,
    )


def test_capacity_initializer_precedes_snapshot_projection():
    """
    Capacity must exist in canonical state before SnapshotService builds the
    first projected NodeSnapshot.
    """

    from app.dashboard.application import (
        NocCapacityInitializer,
    )

    order = []

    resources = Mock()
    resources.captured_at = Mock()

    capacity = Mock()

    capacity_provider = Mock()
    capacity_service = Mock()

    capacity_provider.collect.side_effect = (
        lambda received: (
            order.append("capacity_collect"),
            capacity,
        )[1]
    )

    capacity_service.publish.side_effect = (
        lambda **kwargs: (
            order.append("capacity_publish"),
            capacity,
        )[1]
    )

    initializer = NocCapacityInitializer(
        capacity_provider=capacity_provider,
        capacity_service=capacity_service,
        node_id=Mock(),
        instance_id=Mock(),
    )

    telemetry_refresh_service = Mock()
    telemetry_refresh_service.refresh_from_capture.side_effect = (
        lambda **kwargs: order.append(
            "telemetry"
        )
    )

    snapshot_service = Mock()
    snapshot_service.build.side_effect = (
        lambda *args, **kwargs: (
            order.append("snapshot"),
            Mock(),
        )[1]
    )

    projection = NocSnapshotProjection(
        telemetry_refresh_service=telemetry_refresh_service,
        snapshot_service=snapshot_service,
        node_id=Mock(),
        instance_id=Mock(),
    )

    initializer.initialize_from_capture(
        resources=resources
    )

    projection.project_from_capture(
        resources=resources,
        interface_infos=(),
    )

    assert order == [
        "capacity_collect",
        "capacity_publish",
        "telemetry",
        "snapshot",
    ]
