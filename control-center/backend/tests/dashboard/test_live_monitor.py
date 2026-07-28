"""Pruebas del punto de entrada del monitor NOC."""

from unittest.mock import ANY, Mock, call, patch

from app.dashboard.live_monitor import build_dashboard_application


def test_build_dashboard_application_composes_real_dependencies() -> None:
    """El monitor debe ensamblar todas las dependencias del runtime."""

    settings = Mock()
    settings.mediamtx_api_url = "http://127.0.0.1:9997"
    settings.mediamtx_api_timeout_seconds = 3.0
    settings.mediamtx_metrics_url = "http://127.0.0.1:9998"
    settings.mediamtx_metrics_timeout_seconds = 4.0
    settings.geoip_database_path = (
        "data/geoip/GeoLite2-Country.mmdb"
    )

    api_http_client = Mock()
    metrics_http_client = Mock()

    mediamtx_client = Mock()
    mediamtx_adapter = Mock()

    geoip_service = Mock()
    session_client = Mock()
    session_adapter = Mock()
    session_service = Mock()

    metrics_client = Mock()
    metrics_parser = Mock()
    streaming_health_service = Mock()

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
            side_effect=(
                api_http_client,
                metrics_http_client,
            ),
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
            "app.dashboard.live_monitor.GeoIPService",
            return_value=geoip_service,
        ) as geoip_service_class,
        patch(
            "app.dashboard.live_monitor.MediaMTXSessionClient",
            return_value=session_client,
        ) as session_client_class,
        patch(
            "app.dashboard.live_monitor.MediaMTXSessionAdapter",
            return_value=session_adapter,
        ) as session_adapter_class,
        patch(
            "app.dashboard.live_monitor.SessionService",
            return_value=session_service,
        ) as session_service_class,
        patch(
            "app.dashboard.live_monitor.MediaMTXMetricsClient",
            return_value=metrics_client,
        ) as metrics_client_class,
        patch(
            "app.dashboard.live_monitor.MediaMTXMetricsParser",
            return_value=metrics_parser,
        ) as metrics_parser_class,
        patch(
            "app.dashboard.live_monitor.StreamingHealthService",
            return_value=streaming_health_service,
        ) as health_service_class,
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

    assert http_client_class.call_args_list == [
        call(
            base_url="http://127.0.0.1:9997",
            timeout=3.0,
        ),
        call(
            base_url="http://127.0.0.1:9998",
            timeout=4.0,
            default_headers={
                "Accept": "text/plain",
            },
        ),
    ]

    mediamtx_client_class.assert_called_once_with(
        api_http_client
    )

    mediamtx_adapter_class.assert_called_once_with(
        mediamtx_client
    )

    geoip_service_class.assert_called_once_with(
        "data/geoip/GeoLite2-Country.mmdb"
    )

    session_client_class.assert_called_once_with(
        api_http_client
    )

    session_adapter_class.assert_called_once_with(
        session_client,
        geoip_service,
    )

    session_service_class.assert_called_once_with()

    metrics_client_class.assert_called_once_with(
        metrics_http_client
    )

    metrics_parser_class.assert_called_once_with()
    health_service_class.assert_called_once_with()

    system_adapter_class.assert_called_once_with()

    system_service_class.assert_called_once_with(
        system_adapter
    )

    streaming_service_class.assert_called_once_with()
    dashboard_service_class.assert_called_once_with()
    dashboard_renderer_class.assert_called_once_with()

    dashboard_application_class.assert_called_once_with(
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
        dashboard_snapshot_service=ANY,
    )