"""Pruebas de la aplicación que coordina el dashboard."""

from datetime import datetime, timezone
from unittest.mock import Mock, call, patch

import pytest
from rich.layout import Layout

from app.dashboard.application import DashboardApplication
from app.dashboard.models import DashboardData
from app.dashboard.models.panel_viewport import PanelViewport
from app.dashboard.models.dashboard_navigation_action import (
    DashboardNavigationAction,
)
from app.dashboard.models.dashboard_navigation_state import (
    DashboardNavigationState,
)
from app.dashboard.models.dashboard_navigation_totals import (
    DashboardNavigationTotals,
)
from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    StreamingMeasurement,
)


def test_run_once_builds_and_renders_dashboard() -> None:
    """Una ejecución debe recorrer todo el flujo del dashboard."""

    captured_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=timezone.utc,
    )

    snapshot = MediaMTXSnapshot(
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

    session_snapshot = Mock()
    session_measurement = Mock()

    dashboard_data = Mock(spec=DashboardData)
    rendered_dashboard = Mock(spec=Layout)

    mediamtx_adapter = Mock()
    mediamtx_adapter.health.return_value = True
    mediamtx_adapter.get_snapshot.return_value = snapshot

    session_adapter = Mock()
    session_adapter.get_snapshot.return_value = session_snapshot

    streaming_service = Mock()
    streaming_service.compare.return_value = measurement

    session_service = Mock()
    session_service.measure.return_value = session_measurement

    dashboard_service = Mock()
    dashboard_service.build_dashboard_from_measurement.return_value = (
        dashboard_data
    )

    dashboard_renderer = Mock()
    dashboard_renderer.render.return_value = rendered_dashboard

    system_service = Mock()

    system_info = Mock()
    system_info.hostname = "server-01"
    system_service.get_system_info.return_value = system_info

    system_resources = Mock()
    system_service.get_system_resources.return_value = (
        system_resources
    )

    interface_infos = Mock()
    system_service.get_network_interface_infos.return_value = (
        interface_infos
    )

    network_telemetry = Mock()
    network_interfaces = Mock()

    network_telemetry_service = Mock()
    network_telemetry_service.build.return_value = (
        network_telemetry
    )

    dashboard_service.build_network_interfaces_panel.return_value = (
        network_interfaces
    )

    application = DashboardApplication(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        session_service=session_service,
        dashboard_service=dashboard_service,
        dashboard_renderer=dashboard_renderer,
        system_service=system_service,
        network_telemetry_service=network_telemetry_service,
    )

    result = application.run_once()

    assert result is rendered_dashboard

    mediamtx_adapter.health.assert_called_once_with()
    mediamtx_adapter.get_snapshot.assert_called_once_with()

    session_adapter.get_snapshot.assert_called_once_with()

    streaming_service.compare.assert_called_once_with(
        None,
        snapshot,
    )

    session_service.measure.assert_called_once_with(
        session_snapshot,
    )

    system_service.get_system_info.assert_called_once_with()
    system_service.get_system_resources.assert_called_once_with()

    dashboard_service.build_dashboard_from_measurement.assert_called_once_with(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=snapshot,
        measurement=measurement,
        session_measurement=session_measurement,
        system_resources=system_resources,
        previous_system_resources=None,
        health=None,
        network_interfaces=network_interfaces,
        node_health=None,
        recent_events=None,
        active_alarms=None,
        active_connections_viewport=PanelViewport(
            offset=0,
            page_size=7,
        ),
    )

    dashboard_renderer.render.assert_called_once_with(
        dashboard_data,
        navigation_state=application.navigation_state,
    )


def test_run_once_uses_previous_snapshot_on_second_execution() -> None:
    """La segunda ejecución debe comparar contra el snapshot anterior."""

    first_captured_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=timezone.utc,
    )

    second_captured_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        1,
        tzinfo=timezone.utc,
    )

    first_snapshot = MediaMTXSnapshot(
        captured_at=first_captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    second_snapshot = MediaMTXSnapshot(
        captured_at=second_captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    first_measurement = StreamingMeasurement(
        captured_at=first_captured_at,
        previous_captured_at=None,
        interval_seconds=None,
        paths=(),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    second_measurement = StreamingMeasurement(
        captured_at=second_captured_at,
        previous_captured_at=first_captured_at,
        interval_seconds=1.0,
        paths=(),
        total_inbound_bitrate_bps=0.0,
        total_outbound_bitrate_bps=0.0,
        quality=MeasurementQuality.AVAILABLE,
    )

    first_session_snapshot = Mock()
    second_session_snapshot = Mock()

    first_session_measurement = Mock()
    second_session_measurement = Mock()

    first_dashboard_data = Mock(spec=DashboardData)
    second_dashboard_data = Mock(spec=DashboardData)

    first_layout = Mock(spec=Layout)
    second_layout = Mock(spec=Layout)

    mediamtx_adapter = Mock()
    mediamtx_adapter.health.return_value = True
    mediamtx_adapter.get_snapshot.side_effect = (
        first_snapshot,
        second_snapshot,
    )

    session_adapter = Mock()
    session_adapter.get_snapshot.side_effect = (
        first_session_snapshot,
        second_session_snapshot,
    )

    streaming_service = Mock()
    streaming_service.compare.side_effect = (
        first_measurement,
        second_measurement,
    )

    session_service = Mock()
    session_service.measure.side_effect = (
        first_session_measurement,
        second_session_measurement,
    )

    dashboard_service = Mock()
    dashboard_service.build_dashboard_from_measurement.side_effect = (
        first_dashboard_data,
        second_dashboard_data,
    )

    dashboard_renderer = Mock()
    dashboard_renderer.render.side_effect = (
        first_layout,
        second_layout,
    )

    system_service = Mock()

    system_info = Mock()
    system_info.hostname = "server-01"
    system_service.get_system_info.return_value = system_info

    system_resources = Mock()
    system_service.get_system_resources.return_value = (
        system_resources
    )

    interface_infos = Mock()
    system_service.get_network_interface_infos.return_value = (
        interface_infos
    )

    first_network_telemetry = Mock()
    second_network_telemetry = Mock()

    first_network_interfaces = Mock()
    second_network_interfaces = Mock()

    network_telemetry_service = Mock()
    network_telemetry_service.build.side_effect = (
        first_network_telemetry,
        second_network_telemetry,
    )

    dashboard_service.build_network_interfaces_panel.side_effect = (
        first_network_interfaces,
        second_network_interfaces,
    )

    application = DashboardApplication(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        session_service=session_service,
        dashboard_service=dashboard_service,
        dashboard_renderer=dashboard_renderer,
        system_service=system_service,
        network_telemetry_service=network_telemetry_service,
    )

    first_result = application.run_once()
    second_result = application.run_once()

    assert first_result is first_layout
    assert second_result is second_layout

    assert mediamtx_adapter.get_snapshot.call_count == 2
    assert session_adapter.get_snapshot.call_count == 2

    assert streaming_service.compare.call_count == 2
    assert session_service.measure.call_count == 2

    assert streaming_service.compare.call_args_list[0].args == (
        None,
        first_snapshot,
    )

    assert streaming_service.compare.call_args_list[1].args == (
        first_snapshot,
        second_snapshot,
    )

    assert session_service.measure.call_args_list[0].args == (
        first_session_snapshot,
    )

    assert session_service.measure.call_args_list[1].args == (
        second_session_snapshot,
    )

    assert (
        dashboard_service
        .build_dashboard_from_measurement
        .call_count
        == 2
    )

    assert (
        dashboard_service
        .build_dashboard_from_measurement
        .call_args_list[0]
        .kwargs["session_measurement"]
        is first_session_measurement
    )

    assert (
        dashboard_service
        .build_dashboard_from_measurement
        .call_args_list[1]
        .kwargs["session_measurement"]
        is second_session_measurement
    )

    dashboard_renderer.render.assert_has_calls(
        [
            call(
                first_dashboard_data,
                navigation_state=application.navigation_state,
            ),
            call(
                second_dashboard_data,
                navigation_state=application.navigation_state,
            ),
        ]
    )


def test_run_updates_live_dashboard_repeatedly() -> None:
    """El runtime debe actualizar el mismo Live en cada iteración."""

    application = Mock(spec=DashboardApplication)

    first_layout = Mock(spec=Layout)
    second_layout = Mock(spec=Layout)

    application.run_once.side_effect = (
        first_layout,
        second_layout,
    )

    live_instance = Mock()

    live_context = Mock()
    live_context.__enter__ = Mock(
        return_value=live_instance
    )
    live_context.__exit__ = Mock(
        return_value=False
    )

    with (
        patch(
            "app.dashboard.application.Live",
            return_value=live_context,
        ) as live_class,
        patch(
            "app.dashboard.application.sleep"
        ) as sleep_mock,
    ):
        DashboardApplication.run(
            application,
            refresh_interval_seconds=1.0,
            max_iterations=2,
        )

    live_class.assert_called_once_with(
        screen=True,
        auto_refresh=False,
    )

    assert live_instance.update.call_args_list == [
        call(first_layout, refresh=True),
        call(second_layout, refresh=True),
    ]

    sleep_mock.assert_called_once_with(1.0)


def test_run_once_builds_streaming_health_when_configured() -> None:
    """La aplicación debe ejecutar el flujo completo de salud."""

    from app.adapters.mediamtx.metrics_parser import (
        MediaMTXMetricsSnapshot,
    )
    from app.domain.streaming import (
        HealthStatus,
        StreamingHealth,
    )

    captured_at = datetime(
        2026,
        7,
        22,
        12,
        0,
        tzinfo=timezone.utc,
    )

    snapshot = MediaMTXSnapshot(
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

    session_snapshot = Mock()
    session_measurement = Mock()

    metrics_text = (
        'srt_conns_ms_rtt{id="1",path="enlace"} 10\n'
    )

    metrics_snapshot = MediaMTXMetricsSnapshot(
        samples=(),
    )

    streaming_health = StreamingHealth(
        captured_at=captured_at,
        paths=(),
        status=HealthStatus.UNKNOWN,
        message="No existen métricas SRT disponibles.",
    )

    dashboard_data = Mock(spec=DashboardData)
    rendered_dashboard = Mock(spec=Layout)

    mediamtx_adapter = Mock()
    mediamtx_adapter.health.return_value = True
    mediamtx_adapter.get_snapshot.return_value = snapshot

    session_adapter = Mock()
    session_adapter.get_snapshot.return_value = (
        session_snapshot
    )

    streaming_service = Mock()
    streaming_service.compare.return_value = measurement

    session_service = Mock()
    session_service.measure.return_value = (
        session_measurement
    )

    metrics_client = Mock()
    metrics_client.get_metrics_text.return_value = (
        metrics_text
    )

    metrics_parser = Mock()
    metrics_parser.parse.return_value = (
        metrics_snapshot
    )

    streaming_health_service = Mock()
    streaming_health_service.build.return_value = (
        streaming_health
    )

    dashboard_service = Mock()
    dashboard_service.build_dashboard_from_measurement.return_value = (
        dashboard_data
    )

    dashboard_renderer = Mock()
    dashboard_renderer.render.return_value = (
        rendered_dashboard
    )

    system_service = Mock()

    system_info = Mock()
    system_info.hostname = "server-01"
    system_service.get_system_info.return_value = (
        system_info
    )

    system_resources = Mock()
    system_service.get_system_resources.return_value = (
        system_resources
    )

    interface_infos = Mock()
    system_service.get_network_interface_infos.return_value = (
        interface_infos
    )

    network_telemetry = Mock()
    network_interfaces = Mock()

    network_telemetry_service = Mock()
    network_telemetry_service.build.return_value = (
        network_telemetry
    )

    dashboard_service.build_network_interfaces_panel.return_value = (
        network_interfaces
    )

    application = DashboardApplication(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        session_service=session_service,
        dashboard_service=dashboard_service,
        dashboard_renderer=dashboard_renderer,
        system_service=system_service,
        metrics_client=metrics_client,
        metrics_parser=metrics_parser,
        streaming_health_service=streaming_health_service,
        network_telemetry_service=network_telemetry_service,
    )

    result = application.run_once()

    assert result is rendered_dashboard
    assert application.latest_health is streaming_health

    mediamtx_adapter.health.assert_called_once_with()
    mediamtx_adapter.get_snapshot.assert_called_once_with()

    session_adapter.get_snapshot.assert_called_once_with()

    streaming_service.compare.assert_called_once_with(
        None,
        snapshot,
    )

    session_service.measure.assert_called_once_with(
        session_snapshot,
    )

    metrics_client.get_metrics_text.assert_called_once_with()

    metrics_parser.parse.assert_called_once_with(
        metrics_text
    )

    streaming_health_service.build.assert_called_once_with(
        snapshot=metrics_snapshot,
        captured_at=captured_at,
    )

    dashboard_service.build_dashboard_from_measurement.assert_called_once_with(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=snapshot,
        measurement=measurement,
        session_measurement=session_measurement,
        system_resources=system_resources,
        previous_system_resources=None,
        health=streaming_health,
        network_interfaces=network_interfaces,
        node_health=None,
        recent_events=None,
        active_alarms=None,
        active_connections_viewport=PanelViewport(
            offset=0,
            page_size=7,
        ),
    )

    dashboard_renderer.render.assert_called_once_with(
        dashboard_data,
        navigation_state=application.navigation_state,
    )


def test_application_rejects_partial_health_configuration() -> None:
    """Las dependencias del motor de salud deben configurarse juntas."""

    with pytest.raises(
        ValueError,
        match="deben configurarse juntos",
    ):
        DashboardApplication(
            mediamtx_adapter=Mock(),
            session_adapter=Mock(),
            streaming_service=Mock(),
            session_service=Mock(),
            dashboard_service=Mock(),
            dashboard_renderer=Mock(),
            system_service=Mock(),
            metrics_client=Mock(),
        )

def test_application_transports_node_health_from_noc_runtime() -> None:
    from app.dashboard.models import NodeHealthPanelData
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_instance import NodeInstanceId

    captured_at = datetime(
        2026,
        8,
        18,
        23,
        59,
        tzinfo=timezone.utc,
    )

    snapshot = MediaMTXSnapshot(
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

    session_snapshot = Mock()
    session_measurement = Mock()

    mediamtx_adapter = Mock()
    mediamtx_adapter.health.return_value = True
    mediamtx_adapter.get_snapshot.return_value = snapshot

    session_adapter = Mock()
    session_adapter.get_snapshot.return_value = (
        session_snapshot
    )

    streaming_service = Mock()
    streaming_service.compare.return_value = measurement

    session_service = Mock()
    session_service.measure.return_value = (
        session_measurement
    )

    system_service = Mock()

    system_info = Mock()
    system_info.hostname = "ejtv-01"

    system_resources = Mock()
    interface_infos = Mock()

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
    network_telemetry = Mock()

    network_telemetry_service.build.return_value = (
        network_telemetry
    )

    dashboard_service = Mock()
    network_interfaces = Mock()

    dashboard_service.build_network_interfaces_panel.return_value = (
        network_interfaces
    )

    node_health_panel = NodeHealthPanelData(
        state="WARNING",
        system_state="HEALTHY",
        network_state="WARNING",
        interfaces=(),
        captured_at=captured_at,
    )

    dashboard_service.build_node_health_panel.return_value = (
        node_health_panel
    )

    health_diagnostic = Mock()

    health_diagnostic_repository = Mock()
    health_diagnostic_repository.latest.return_value = (
        health_diagnostic
    )

    event_service = Mock()
    alarm_service = Mock()

    event_records = (
        Mock(),
        Mock(),
    )

    event_history_records = tuple(
        Mock(event=event)
        for event in event_records
    )

    alarm_records = (
        Mock(),
        Mock(),
    )

    history_query_service = Mock()
    history_query_service.recent_events.return_value = (
        event_history_records
    )
    history_query_service.active_alarms.return_value = (
        alarm_records
    )

    recent_events_panel = Mock()
    dashboard_service.build_recent_events_panel.return_value = (
        recent_events_panel
    )

    active_alarms_panel = Mock()
    dashboard_service.build_active_alarms_panel.return_value = (
        active_alarms_panel
    )

    dashboard_data = Mock(spec=DashboardData)

    dashboard_data.active_connections = Mock()
    dashboard_data.active_connections.total_items = 10

    dashboard_data.active_alarms = Mock()
    dashboard_data.active_alarms.total_items = 8

    dashboard_data.recent_events = Mock()
    dashboard_data.recent_events.total_items = 20

    dashboard_snapshot_service = Mock()
    dashboard_snapshot_service.build_snapshot.return_value = (
        dashboard_data
    )

    dashboard_renderer = Mock()

    node_id = NodeId.create(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
    )

    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    navigation_state = DashboardNavigationState(
        active_connections=PanelViewport(
            offset=4,
            page_size=7,
        ),
        active_alarms=PanelViewport(
            offset=8,
            page_size=5,
        ),
        recent_events=PanelViewport(
            offset=12,
            page_size=5,
        ),
    )

    application = DashboardApplication(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        session_service=session_service,
        dashboard_service=dashboard_service,
        dashboard_renderer=dashboard_renderer,
        system_service=system_service,
        dashboard_snapshot_service=dashboard_snapshot_service,
        network_telemetry_service=network_telemetry_service,
        health_diagnostic_repository=health_diagnostic_repository,
        event_service=event_service,
        alarm_service=alarm_service,
        history_query_service=history_query_service,
        node_id=node_id,
        instance_id=instance_id,
        navigation_state=navigation_state,
    )

    result = application.build_dashboard()

    assert result is dashboard_data

    health_diagnostic_repository.latest.assert_called_once_with(
        node_id=node_id,
        instance_id=instance_id,
    )

    dashboard_service.build_node_health_panel.assert_called_once_with(
        diagnostic=health_diagnostic,
    )

    event_service.list_all.assert_not_called()

    history_query_service.recent_events.assert_called_once_with(
        node_id=node_id,
        instance_id=instance_id,
    )

    dashboard_service.build_recent_events_panel.assert_called_once_with(
        events=event_records,
        viewport=PanelViewport(
            offset=12,
            page_size=5,
        ),
    )

    alarm_service.active.assert_not_called()

    history_query_service.active_alarms.assert_called_once_with(
        node_id=node_id,
        instance_id=instance_id,
    )

    dashboard_service.build_active_alarms_panel.assert_called_once_with(
        alarms=alarm_records,
        viewport=PanelViewport(
            offset=8,
            page_size=5,
        ),
    )

    snapshot_input = (
        dashboard_snapshot_service
        .build_snapshot
        .call_args
        .args[0]
    )

    assert snapshot_input.node_health is node_health_panel
    assert snapshot_input.recent_events is recent_events_panel
    assert snapshot_input.active_alarms is active_alarms_panel
    assert snapshot_input.active_connections_viewport == PanelViewport(
        offset=4,
        page_size=7,
    )

    assert application.navigation_state == navigation_state

    assert application.navigation_totals.active_connections == 10
    assert application.navigation_totals.active_alarms == 8
    assert application.navigation_totals.recent_events == 20

    application.apply_navigation_action(
        DashboardNavigationAction.SCROLL_DOWN
    )

    assert application.navigation_state.active_connections == PanelViewport(
        offset=3,
        page_size=7,
    )
    assert application.navigation_state.active_alarms == PanelViewport(
        offset=8,
        page_size=5,
    )
    assert application.navigation_state.recent_events == PanelViewport(
        offset=12,
        page_size=5,
    )

    application.apply_navigation_action(
        DashboardNavigationAction.NEXT_PANEL
    )

    assert application.navigation_state.active_panel.value == (
        "active_alarms"
    )

    assert application.navigation_state.active_connections == PanelViewport(
        offset=3,
        page_size=7,
    )
    assert application.navigation_state.active_alarms == PanelViewport(
        offset=8,
        page_size=5,
    )
    assert application.navigation_state.recent_events == PanelViewport(
        offset=12,
        page_size=5,
    )

    # --------------------------------------------------------
    # Segundo refresh: los tres viewports deben conservarse.
    # --------------------------------------------------------

    second_result = application.build_dashboard()

    assert second_result is dashboard_data

    assert application.navigation_state.active_panel.value == (
        "active_alarms"
    )
    assert application.navigation_state.active_connections == PanelViewport(
        offset=3,
        page_size=7,
    )
    assert application.navigation_state.active_alarms == PanelViewport(
        offset=8,
        page_size=5,
    )
    assert application.navigation_state.recent_events == PanelViewport(
        offset=12,
        page_size=5,
    )

    recent_event_calls = (
        dashboard_service
        .build_recent_events_panel
        .call_args_list
    )

    assert len(recent_event_calls) == 2
    assert recent_event_calls[0].kwargs["viewport"] == PanelViewport(
        offset=12,
        page_size=5,
    )
    assert recent_event_calls[1].kwargs["viewport"] == PanelViewport(
        offset=12,
        page_size=5,
    )

    active_alarm_calls = (
        dashboard_service
        .build_active_alarms_panel
        .call_args_list
    )

    assert len(active_alarm_calls) == 2
    assert active_alarm_calls[0].kwargs["viewport"] == PanelViewport(
        offset=8,
        page_size=5,
    )
    assert active_alarm_calls[1].kwargs["viewport"] == PanelViewport(
        offset=8,
        page_size=5,
    )

    snapshot_calls = (
        dashboard_snapshot_service
        .build_snapshot
        .call_args_list
    )

    assert len(snapshot_calls) == 2

    first_snapshot_input = snapshot_calls[0].args[0]
    second_snapshot_input = snapshot_calls[1].args[0]

    assert first_snapshot_input.active_connections_viewport == PanelViewport(
        offset=4,
        page_size=7,
    )
    assert second_snapshot_input.active_connections_viewport == PanelViewport(
        offset=3,
        page_size=7,
    )



def test_application_reads_durable_history_without_noc_runtime() -> None:
    """El dashboard puede leer historia durable sin poseer el runtime NOC."""
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_instance import NodeInstanceId

    captured_at = datetime(
        2026,
        8,
        18,
        23,
        59,
        tzinfo=timezone.utc,
    )

    snapshot = MediaMTXSnapshot(
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

    session_snapshot = Mock()
    session_measurement = Mock()

    mediamtx_adapter = Mock()
    mediamtx_adapter.health.return_value = True
    mediamtx_adapter.get_snapshot.return_value = snapshot

    session_adapter = Mock()
    session_adapter.get_snapshot.return_value = session_snapshot

    streaming_service = Mock()
    streaming_service.compare.return_value = measurement

    session_service = Mock()
    session_service.measure.return_value = session_measurement

    system_service = Mock()

    system_info = Mock()
    system_info.hostname = "ejtv-01"

    system_resources = Mock()
    interface_infos = Mock()

    system_service.get_system_info.return_value = system_info
    system_service.get_system_resources.return_value = system_resources
    system_service.get_network_interface_infos.return_value = interface_infos

    network_telemetry_service = Mock()
    network_telemetry_service.build.return_value = Mock()

    dashboard_service = Mock()
    dashboard_service.build_network_interfaces_panel.return_value = Mock()

    event_records = (
        Mock(),
        Mock(),
    )

    event_history_records = tuple(
        Mock(event=event)
        for event in event_records
    )

    alarm_records = (
        Mock(),
        Mock(),
    )

    history_query_service = Mock()
    history_query_service.recent_events.return_value = (
        event_history_records
    )
    history_query_service.active_alarms.return_value = alarm_records

    recent_events_panel = Mock()
    active_alarms_panel = Mock()

    dashboard_service.build_recent_events_panel.return_value = (
        recent_events_panel
    )
    dashboard_service.build_active_alarms_panel.return_value = (
        active_alarms_panel
    )

    dashboard_data = Mock(spec=DashboardData)

    dashboard_data.active_connections = Mock()
    dashboard_data.active_connections.total_items = 0

    dashboard_data.active_alarms = Mock()
    dashboard_data.active_alarms.total_items = 2

    dashboard_data.recent_events = Mock()
    dashboard_data.recent_events.total_items = 2

    dashboard_snapshot_service = Mock()
    dashboard_snapshot_service.build_snapshot.return_value = dashboard_data

    node_id = NodeId.create(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
    )

    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    application = DashboardApplication(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        session_service=session_service,
        dashboard_service=dashboard_service,
        dashboard_renderer=Mock(),
        system_service=system_service,
        dashboard_snapshot_service=dashboard_snapshot_service,
        network_telemetry_service=network_telemetry_service,
        history_query_service=history_query_service,
        node_id=node_id,
        instance_id=instance_id,
    )

    result = application.build_dashboard()

    assert result is dashboard_data

    history_query_service.recent_events.assert_called_once_with(
        node_id=node_id,
        instance_id=instance_id,
    )

    history_query_service.active_alarms.assert_called_once_with(
        node_id=node_id,
        instance_id=instance_id,
    )

    dashboard_service.build_recent_events_panel.assert_called_once_with(
        events=event_records,
        viewport=PanelViewport(
            offset=0,
            page_size=5,
        ),
    )

    dashboard_service.build_active_alarms_panel.assert_called_once_with(
        alarms=alarm_records,
        viewport=PanelViewport(
            offset=0,
            page_size=5,
        ),
    )

    snapshot_input = (
        dashboard_snapshot_service
        .build_snapshot
        .call_args
        .args[0]
    )

    assert snapshot_input.node_health is None
    assert snapshot_input.recent_events is recent_events_panel
    assert snapshot_input.active_alarms is active_alarms_panel


def test_application_keeps_node_health_empty_when_shared_diagnostic_is_absent() -> None:
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_instance import NodeInstanceId

    captured_at = datetime(
        2026,
        8,
        18,
        23,
        59,
        tzinfo=timezone.utc,
    )

    snapshot = MediaMTXSnapshot(
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

    mediamtx_adapter = Mock()
    mediamtx_adapter.health.return_value = True
    mediamtx_adapter.get_snapshot.return_value = snapshot

    session_adapter = Mock()
    session_adapter.get_snapshot.return_value = Mock()

    streaming_service = Mock()
    streaming_service.compare.return_value = measurement

    session_service = Mock()
    session_service.measure.return_value = Mock()

    system_service = Mock()

    system_info = Mock()
    system_info.hostname = "ejtv-01"

    system_resources = Mock()
    interface_infos = Mock()

    system_service.get_system_info.return_value = system_info
    system_service.get_system_resources.return_value = system_resources
    system_service.get_network_interface_infos.return_value = interface_infos

    network_telemetry_service = Mock()
    network_telemetry_service.build.return_value = Mock()

    dashboard_service = Mock()
    dashboard_service.build_network_interfaces_panel.return_value = Mock()

    health_diagnostic_repository = Mock()
    health_diagnostic_repository.latest.return_value = None

    dashboard_data = Mock(spec=DashboardData)

    dashboard_data.active_connections = Mock()
    dashboard_data.active_connections.total_items = 0
    dashboard_data.active_alarms = None
    dashboard_data.recent_events = None

    dashboard_snapshot_service = Mock()
    dashboard_snapshot_service.build_snapshot.return_value = (
        dashboard_data
    )

    node_id = NodeId.create(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
    )

    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    application = DashboardApplication(
        mediamtx_adapter=mediamtx_adapter,
        session_adapter=session_adapter,
        streaming_service=streaming_service,
        session_service=session_service,
        dashboard_service=dashboard_service,
        dashboard_renderer=Mock(),
        system_service=system_service,
        dashboard_snapshot_service=dashboard_snapshot_service,
        network_telemetry_service=network_telemetry_service,
        health_diagnostic_repository=health_diagnostic_repository,
        node_id=node_id,
        instance_id=instance_id,
    )

    result = application.build_dashboard()

    assert result is dashboard_data

    health_diagnostic_repository.latest.assert_called_once_with(
        node_id=node_id,
        instance_id=instance_id,
    )

    dashboard_service.build_node_health_panel.assert_not_called()

    snapshot_input = (
        dashboard_snapshot_service
        .build_snapshot
        .call_args
        .args[0]
    )

    assert snapshot_input.node_health is None


@pytest.mark.parametrize(
    (
        "node_id",
        "instance_id",
    ),
    (
        (Mock(), None),
        (None, Mock()),
    ),
)
def test_application_rejects_partial_noc_identity(
    node_id,
    instance_id,
) -> None:
    with pytest.raises(
        ValueError,
        match="node_id e instance_id deben configurarse juntos",
    ):
        DashboardApplication(
            mediamtx_adapter=Mock(),
            session_adapter=Mock(),
            streaming_service=Mock(),
            session_service=Mock(),
            dashboard_service=Mock(),
            dashboard_renderer=Mock(),
            system_service=Mock(),
            node_id=node_id,
            instance_id=instance_id,
        )


@pytest.mark.parametrize(
    "reader_name",
    (
        "history_query_service",
        "health_diagnostic_repository",
    ),
)
def test_application_rejects_noc_reader_without_identity(
    reader_name,
) -> None:
    kwargs = {
        reader_name: Mock(),
    }

    with pytest.raises(
        ValueError,
        match="dependencias de lectura NOC requieren",
    ):
        DashboardApplication(
            mediamtx_adapter=Mock(),
            session_adapter=Mock(),
            streaming_service=Mock(),
            session_service=Mock(),
            dashboard_service=Mock(),
            dashboard_renderer=Mock(),
            system_service=Mock(),
            **kwargs,
        )


@pytest.mark.parametrize(
    (
        "event_service",
        "alarm_service",
    ),
    (
        (Mock(), None),
        (None, Mock()),
    ),
)
def test_application_rejects_partial_operational_noc_configuration(
    event_service,
    alarm_service,
) -> None:
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_instance import NodeInstanceId

    node_id = NodeId.create(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
    )
    instance_id = NodeInstanceId("streaming-primary")

    with pytest.raises(
        ValueError,
        match="event_service y alarm_service deben configurarse juntos",
    ):
        DashboardApplication(
            mediamtx_adapter=Mock(),
            session_adapter=Mock(),
            streaming_service=Mock(),
            session_service=Mock(),
            dashboard_service=Mock(),
            dashboard_renderer=Mock(),
            system_service=Mock(),
            event_service=event_service,
            alarm_service=alarm_service,
            node_id=node_id,
            instance_id=instance_id,
        )


def test_run_quit_key_stops_before_next_refresh() -> None:
    """q debe terminar el runtime sin ejecutar otra captura."""

    application = DashboardApplication(
        mediamtx_adapter=Mock(),
        session_adapter=Mock(),
        streaming_service=Mock(),
        session_service=Mock(),
        dashboard_service=Mock(),
        dashboard_renderer=Mock(),
        system_service=Mock(),
    )

    first_layout = Mock(spec=Layout)

    application.run_once = Mock(
        return_value=first_layout
    )

    keyboard_input = Mock()
    keyboard_input.active = True
    keyboard_input.__enter__ = Mock(
        return_value=keyboard_input
    )
    keyboard_input.__exit__ = Mock(
        return_value=False
    )
    keyboard_input.read_available.return_value = b"q"

    application._keyboard_input = keyboard_input

    live_instance = Mock()

    live_context = Mock()
    live_context.__enter__ = Mock(
        return_value=live_instance
    )
    live_context.__exit__ = Mock(
        return_value=False
    )

    with (
        patch(
            "app.dashboard.application.Live",
            return_value=live_context,
        ),
        patch(
            "app.dashboard.application.monotonic",
            side_effect=(0.0, 0.1),
        ),
    ):
        application.run(
            refresh_interval_seconds=1.0,
            max_iterations=2,
        )

    application.run_once.assert_called_once_with()

    live_instance.update.assert_called_once_with(
        first_layout,
        refresh=True,
    )

    keyboard_input.read_available.assert_called_once_with(
        timeout_seconds=0.9,
    )


def test_run_navigation_key_preserves_normal_refresh_cadence() -> None:
    """Una tecla de navegación no debe provocar una captura extra."""

    application = DashboardApplication(
        mediamtx_adapter=Mock(),
        session_adapter=Mock(),
        streaming_service=Mock(),
        session_service=Mock(),
        dashboard_service=Mock(),
        dashboard_renderer=Mock(),
        system_service=Mock(),
    )

    first_layout = Mock(spec=Layout)
    second_layout = Mock(spec=Layout)

    application.run_once = Mock(
        side_effect=(
            first_layout,
            second_layout,
        )
    )

    application._navigation_totals = DashboardNavigationTotals(
        active_connections=20,
        active_alarms=0,
        recent_events=0,
    )

    keyboard_input = Mock()
    keyboard_input.active = True
    keyboard_input.__enter__ = Mock(
        return_value=keyboard_input
    )
    keyboard_input.__exit__ = Mock(
        return_value=False
    )
    keyboard_input.read_available.side_effect = (
        b"\x1b[B",
        None,
    )

    application._keyboard_input = keyboard_input

    live_instance = Mock()

    live_context = Mock()
    live_context.__enter__ = Mock(
        return_value=live_instance
    )
    live_context.__exit__ = Mock(
        return_value=False
    )

    with (
        patch(
            "app.dashboard.application.Live",
            return_value=live_context,
        ),
        patch(
            "app.dashboard.application.monotonic",
            side_effect=(
                0.0,
                0.1,
                0.2,
            ),
        ),
    ):
        application.run(
            refresh_interval_seconds=1.0,
            max_iterations=2,
        )

    assert application.run_once.call_count == 2

    assert live_instance.update.call_args_list == [
        call(first_layout, refresh=True),
        call(second_layout, refresh=True),
    ]

    assert (
        application.navigation_state.active_connections.offset
        == 1
    )

    assert keyboard_input.read_available.call_args_list == [
        call(timeout_seconds=0.9),
        call(timeout_seconds=0.8),
    ]


def test_run_multiple_navigation_keys_do_not_add_refreshes() -> None:
    """Varias teclas dentro del intervalo no deben recapturar telemetría."""

    application = DashboardApplication(
        mediamtx_adapter=Mock(),
        session_adapter=Mock(),
        streaming_service=Mock(),
        session_service=Mock(),
        dashboard_service=Mock(),
        dashboard_renderer=Mock(),
        system_service=Mock(),
    )

    first_layout = Mock(spec=Layout)
    second_layout = Mock(spec=Layout)

    application.run_once = Mock(
        side_effect=(
            first_layout,
            second_layout,
        )
    )

    application._navigation_totals = DashboardNavigationTotals(
        active_connections=20,
        active_alarms=20,
        recent_events=20,
    )

    keyboard_input = Mock()
    keyboard_input.active = True
    keyboard_input.__enter__ = Mock(
        return_value=keyboard_input
    )
    keyboard_input.__exit__ = Mock(
        return_value=False
    )
    keyboard_input.read_available.side_effect = (
        b"\x1b[B",
        b"\x1b[B",
        b"\t",
        b"\x1b[6~",
        None,
    )

    application._keyboard_input = keyboard_input

    live_instance = Mock()

    live_context = Mock()
    live_context.__enter__ = Mock(
        return_value=live_instance
    )
    live_context.__exit__ = Mock(
        return_value=False
    )

    with (
        patch(
            "app.dashboard.application.Live",
            return_value=live_context,
        ),
        patch(
            "app.dashboard.application.monotonic",
            side_effect=(
                0.0,
                0.1,
                0.2,
                0.3,
                0.4,
                0.5,
            ),
        ),
    ):
        application.run(
            refresh_interval_seconds=1.0,
            max_iterations=2,
        )

    assert application.run_once.call_count == 2

    assert (
        application.navigation_state.active_connections.offset
        == 2
    )

    assert (
        application.navigation_state.active_panel.value
        == "active_alarms"
    )

    assert (
        application.navigation_state.active_alarms.offset
        == 5
    )


def test_run_once_passes_current_navigation_state_to_renderer() -> None:
    """El renderer debe recibir el estado UI vigente de la aplicación."""

    from app.dashboard.models.dashboard_navigation_state import (
        DashboardNavigationState,
        NavigablePanel,
    )
    from app.dashboard.models.panel_viewport import PanelViewport

    application = Mock(spec=DashboardApplication)

    navigation_state = DashboardNavigationState(
        active_panel=NavigablePanel.RECENT_EVENTS,
        active_connections=PanelViewport(
            offset=3,
            page_size=7,
        ),
        active_alarms=PanelViewport(
            offset=5,
            page_size=5,
        ),
        recent_events=PanelViewport(
            offset=10,
            page_size=5,
        ),
    )

    dashboard_data = Mock(spec=DashboardData)
    rendered_dashboard = Mock(spec=Layout)

    application.build_dashboard.return_value = dashboard_data
    application._dashboard_renderer = Mock()
    application._dashboard_renderer.render.return_value = (
        rendered_dashboard
    )
    application._navigation_state = navigation_state

    result = DashboardApplication.run_once(application)

    assert result is rendered_dashboard

    application._dashboard_renderer.render.assert_called_once_with(
        dashboard_data,
        navigation_state=navigation_state,
    )
