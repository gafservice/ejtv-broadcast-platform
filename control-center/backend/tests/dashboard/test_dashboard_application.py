"""Pruebas de la aplicación que coordina el dashboard."""

from datetime import datetime, timezone
from unittest.mock import Mock, call, patch
from rich.layout import Layout

from app.dashboard.application import DashboardApplication
from app.dashboard.models import DashboardData
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

    dashboard_data = Mock(spec=DashboardData)
    rendered_dashboard = Mock(spec=Layout)

    mediamtx_adapter = Mock()
    mediamtx_adapter.health.return_value = True
    mediamtx_adapter.get_snapshot.return_value = snapshot

    streaming_service = Mock()
    streaming_service.compare.return_value = measurement

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

    application = DashboardApplication(
        mediamtx_adapter=mediamtx_adapter,
        streaming_service=streaming_service,
        dashboard_service=dashboard_service,
        dashboard_renderer=dashboard_renderer,
        system_service=system_service,
    )

    result = application.run_once()

    assert result is rendered_dashboard

    mediamtx_adapter.health.assert_called_once_with()
    mediamtx_adapter.get_snapshot.assert_called_once_with()

    streaming_service.compare.assert_called_once_with(
        None,
        snapshot,
    )

    system_service.get_system_info.assert_called_once_with()

    dashboard_service.build_dashboard_from_measurement.assert_called_once_with(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=snapshot,
        measurement=measurement,
    )

    dashboard_renderer.render.assert_called_once_with(dashboard_data)
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

    streaming_service = Mock()
    streaming_service.compare.side_effect = (
        first_measurement,
        second_measurement,
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

    application = DashboardApplication(
        mediamtx_adapter=mediamtx_adapter,
        streaming_service=streaming_service,
        dashboard_service=dashboard_service,
        dashboard_renderer=dashboard_renderer,
        system_service=system_service,
    )

    first_result = application.run_once()
    second_result = application.run_once()

    assert first_result is first_layout
    assert second_result is second_layout

    assert streaming_service.compare.call_count == 2

    assert streaming_service.compare.call_args_list[0].args == (
        None,
        first_snapshot,
    )

    assert streaming_service.compare.call_args_list[1].args == (
        first_snapshot,
        second_snapshot,
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
    live_context.__enter__ = Mock(return_value=live_instance)
    live_context.__exit__ = Mock(return_value=False)

    with (
        patch(
            "app.dashboard.application.Live",
            return_value=live_context,
        ) as live_class,
        patch("app.dashboard.application.sleep") as sleep_mock,
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
    from app.domain.streaming import HealthStatus, StreamingHealth

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

    metrics_text = 'srt_conns_ms_rtt{id="1",path="enlace"} 10\n'

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

    streaming_service = Mock()
    streaming_service.compare.return_value = measurement

    metrics_client = Mock()
    metrics_client.get_metrics_text.return_value = metrics_text

    metrics_parser = Mock()
    metrics_parser.parse.return_value = metrics_snapshot

    streaming_health_service = Mock()
    streaming_health_service.build.return_value = streaming_health

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

    application = DashboardApplication(
        mediamtx_adapter=mediamtx_adapter,
        streaming_service=streaming_service,
        dashboard_service=dashboard_service,
        dashboard_renderer=dashboard_renderer,
        system_service=system_service,
        metrics_client=metrics_client,
        metrics_parser=metrics_parser,
        streaming_health_service=streaming_health_service,
    )

    result = application.run_once()

    assert result is rendered_dashboard
    assert application.latest_health is streaming_health

    metrics_client.get_metrics_text.assert_called_once_with()
    metrics_parser.parse.assert_called_once_with(metrics_text)

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
        health=streaming_health,
    )


def test_application_rejects_partial_health_configuration() -> None:
    """Las dependencias del motor de salud deben configurarse juntas."""

    import pytest

    with pytest.raises(
        ValueError,
        match="deben configurarse juntos",
    ):
        DashboardApplication(
            mediamtx_adapter=Mock(),
            streaming_service=Mock(),
            dashboard_service=Mock(),
            dashboard_renderer=Mock(),
            system_service=Mock(),
            metrics_client=Mock(),
        )
