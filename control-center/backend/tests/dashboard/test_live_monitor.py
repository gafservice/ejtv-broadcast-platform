"""Pruebas del punto de entrada del monitor NOC."""

from unittest.mock import Mock, patch

from app.dashboard.live_monitor import build_dashboard_application


def test_build_dashboard_application_composes_real_dependencies() -> None:
    """El monitor debe ensamblar todas las dependencias del runtime."""

    settings = Mock()
    settings.mediamtx_api_url = "http://127.0.0.1:9997"
    settings.mediamtx_api_timeout_seconds = 3.0

    http_client = Mock()
    mediamtx_client = Mock()
    mediamtx_adapter = Mock()
    system_adapter = Mock()
    system_service = Mock()
    streaming_service = Mock()
    dashboard_service = Mock()
    dashboard_renderer = Mock()
    dashboard_application = Mock()

    with (
        patch(
            "app.dashboard.live_monitor.get_settings",
            return_value=settings,
        ),
        patch(
            "app.dashboard.live_monitor.HttpClient",
            return_value=http_client,
        ) as http_client_class,
        patch(
            "app.dashboard.live_monitor.MediaMTXClient",
            return_value=mediamtx_client,
        ) as mediamtx_client_class,
        patch(
            "app.dashboard.live_monitor.MediaMTXAdapter",
            return_value=mediamtx_adapter,
        ) as mediamtx_adapter_class,
        patch(
            "app.dashboard.live_monitor.LinuxSystemAdapter",
            return_value=system_adapter,
        ) as system_adapter_class,
        patch(
            "app.dashboard.live_monitor.SystemService",
            return_value=system_service,
        ) as system_service_class,
        patch(
            "app.dashboard.live_monitor.StreamingService",
            return_value=streaming_service,
        ) as streaming_service_class,
        patch(
            "app.dashboard.live_monitor.DashboardService",
            return_value=dashboard_service,
        ) as dashboard_service_class,
        patch(
            "app.dashboard.live_monitor.DashboardRenderer",
            return_value=dashboard_renderer,
        ) as dashboard_renderer_class,
        patch(
            "app.dashboard.live_monitor.DashboardApplication",
            return_value=dashboard_application,
        ) as dashboard_application_class,
    ):
        result = build_dashboard_application()

    assert result is dashboard_application

    http_client_class.assert_called_once_with(
        base_url="http://127.0.0.1:9997",
        timeout=3.0,
    )

    mediamtx_client_class.assert_called_once_with(http_client)
    mediamtx_adapter_class.assert_called_once_with(mediamtx_client)

    system_adapter_class.assert_called_once_with()
    system_service_class.assert_called_once_with(system_adapter)

    streaming_service_class.assert_called_once_with()
    dashboard_service_class.assert_called_once_with()
    dashboard_renderer_class.assert_called_once_with()

    dashboard_application_class.assert_called_once_with(
        mediamtx_adapter=mediamtx_adapter,
        streaming_service=streaming_service,
        dashboard_service=dashboard_service,
        dashboard_renderer=dashboard_renderer,
        system_service=system_service,
    )

