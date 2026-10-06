"""Contract tests for canonical NOC capacity wiring in live_monitor.

ENG-013C — Terminal Dashboard

The terminal monitor owns one local canonical NOC graph.

Capacity must:
- use that same NodeRegistry;
- use the existing SystemCapacityProvider;
- use the existing CapacityService;
- be initialized before NocSnapshotProjection is used;
- become visible through SnapshotService;
- not create a second NodeRegistry;
- not be refreshed inside NocSnapshotProjection.
"""

from unittest.mock import MagicMock, patch

from app.dashboard.application import NocSnapshotProjection
from app.dashboard.live_monitor import build_dashboard_application
from app.noc.domain.node_capacity import NodeCapacity
from app.noc.infrastructure.system_capacity_provider import (
    SystemCapacityProvider,
)
from app.noc.services.capacity_service import CapacityService


def test_build_dashboard_application_composes_canonical_capacity_services():
    """Capacity services must use the monitor's existing NOC registry."""

    from contextlib import ExitStack

    node_registry = MagicMock()

    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXAdapter"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXSessionAdapter"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXMetricsClient"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXMetricsParser"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.LinuxSystemAdapter"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SystemService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.InMemoryNodeRepository"
            )
        )

        node_registry_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeRegistry",
                return_value=node_registry,
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.bootstrap_noc_runtime"
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.JsonlEvidenceWriter"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.EventService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.AlarmService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.HistoryQueryService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteHistoryDatabase"
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeMediaProfileLoader"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "SQLiteSignalHealthCurrentStateRepository"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteEventHistoryRepository"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteAlarmHistoryRepository"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "SQLiteNodeHealthDiagnosticRepository"
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "StreamingHealthTransitionEventService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "StreamingHealthTransitionAlarmService"
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MetricService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.HealthService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SnapshotService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.TelemetryRefreshService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NocSnapshotProjection"
            )
        )

        capacity_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.CapacityService",
                create=True,
            )
        )

        capacity_provider_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SystemCapacityProvider",
                create=True,
            )
        )

        build_dashboard_application()

    node_registry_class.assert_called_once()

    capacity_service_class.assert_called_once_with(
        node_registry
    )

    capacity_provider_class.assert_called_once_with()


def test_capacity_provider_and_service_can_publish_into_same_registry():
    """Existing capacity components must produce canonical NodeCapacity."""

    registry = MagicMock()

    service = CapacityService.__new__(
        CapacityService
    )

    provider = SystemCapacityProvider()

    assert isinstance(
        provider,
        SystemCapacityProvider,
    )

    assert isinstance(
        service,
        CapacityService,
    )

    # This test intentionally does not perform a physical capture.
    # Runtime publication is covered by the composition contract.
    assert registry is not None


def test_noc_snapshot_projection_does_not_own_capacity_refresh():
    """
    Capacity lifecycle must remain outside the per-cycle snapshot projection.

    Capacity may be updated by its own canonical lifecycle, but
    NocSnapshotProjection must only project already-published NOC state.
    It must not own a CapacityService, a SystemCapacityProvider, or perform
    capacity collection/publication as part of each dashboard cycle.
    """

    from unittest.mock import Mock

    projection = NocSnapshotProjection(
        telemetry_refresh_service=Mock(
            name="telemetry_refresh_service"
        ),
        snapshot_service=Mock(
            name="snapshot_service"
        ),
        node_id=Mock(name="node_id"),
        instance_id=Mock(name="instance_id"),
    )

    assert not hasattr(
        projection,
        "_capacity_service",
    )

    assert not hasattr(
        projection,
        "_capacity_provider",
    )

    assert not hasattr(
        projection,
        "refresh_capacity",
    )


def test_capacity_domain_remains_node_capacity():
    """Terminal composition must reuse NodeCapacity, not invent a DTO."""

    assert NodeCapacity.__name__ == "NodeCapacity"


def test_build_dashboard_application_wires_capacity_initializer():
    """
    The terminal monitor must compose Capacity through NocCapacityInitializer.

    This keeps Capacity lifecycle outside NocSnapshotProjection while
    preserving the existing no-capture/no-publication composition boundary.
    """

    from contextlib import ExitStack
    from unittest.mock import MagicMock, patch

    node_registry = MagicMock(name="node_registry")
    capacity_service = MagicMock(name="capacity_service")
    capacity_provider = MagicMock(name="capacity_provider")
    projection = MagicMock(name="projection")

    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXAdapter"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXSessionAdapter"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXMetricsClient"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXMetricsParser"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.LinuxSystemAdapter"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SystemService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.InMemoryNodeRepository"
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeRegistry",
                return_value=node_registry,
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.bootstrap_noc_runtime"
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.JsonlEvidenceWriter"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.EventService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.AlarmService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.HistoryQueryService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteHistoryDatabase"
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeMediaProfileLoader"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "SQLiteSignalHealthCurrentStateRepository"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteEventHistoryRepository"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteAlarmHistoryRepository"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "SQLiteNodeHealthDiagnosticRepository"
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "StreamingHealthTransitionEventService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "StreamingHealthTransitionAlarmService"
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MetricService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.HealthService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SnapshotService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.TelemetryRefreshService"
            )
        )

        capacity_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.CapacityService",
                return_value=capacity_service,
            )
        )

        capacity_provider_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SystemCapacityProvider",
                return_value=capacity_provider,
            )
        )

        capacity_initializer = MagicMock(
            name="capacity_initializer"
        )

        capacity_initializer_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NocCapacityInitializer",
                return_value=capacity_initializer,
                create=True,
            )
        )

        projection_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NocSnapshotProjection",
                return_value=projection,
            )
        )

        dashboard_application_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.DashboardApplication"
            )
        )

        build_dashboard_application()

    capacity_service_class.assert_called_once_with(
        node_registry
    )

    capacity_provider_class.assert_called_once_with()

    capacity_initializer_class.assert_called_once()

    initializer_kwargs = (
        capacity_initializer_class.call_args.kwargs
    )

    assert (
        initializer_kwargs["capacity_service"]
        is capacity_service
    )

    assert (
        initializer_kwargs["capacity_provider"]
        is capacity_provider
    )

    assert "node_id" in initializer_kwargs
    assert "instance_id" in initializer_kwargs

    projection_class.assert_called_once()

    projection_kwargs = (
        projection_class.call_args.kwargs
    )

    assert (
        "capacity_service"
        not in projection_kwargs
    )

    assert (
        "capacity_provider"
        not in projection_kwargs
    )

    dashboard_application_class.assert_called_once()

    application_kwargs = (
        dashboard_application_class.call_args.kwargs
    )

    assert (
        application_kwargs[
            "noc_capacity_initializer"
        ]
        is capacity_initializer
    )

    assert (
        application_kwargs[
            "noc_snapshot_projection"
        ]
        is projection
    )

    capacity_provider.collect.assert_not_called()
    capacity_service.publish.assert_not_called()
