"""Pruebas del punto de entrada del monitor NOC."""

from contextlib import ExitStack
from unittest.mock import ANY, Mock, call, patch

from app.dashboard.live_monitor import build_dashboard_application


def test_build_dashboard_application_composes_shared_read_dependencies() -> None:
    """El terminal debe leer el NOC compartido sin poseer su runtime."""

    settings = Mock()
    settings.mediamtx_api_url = "http://127.0.0.1:9997"
    settings.mediamtx_api_timeout_seconds = 3.0
    settings.mediamtx_metrics_url = "http://127.0.0.1:9998"
    settings.mediamtx_metrics_timeout_seconds = 4.0
    settings.geoip_database_path = (
        "data/geoip/GeoLite2-Country.mmdb"
    )
    settings.noc_history_database_path = (
        "/tmp/noc-history.db"
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
    network_telemetry_service = Mock()

    node_id = Mock()
    node_instance_id = Mock()

    history_database = Mock()
    event_history_repository = Mock()
    alarm_history_repository = Mock()
    history_query_service = Mock()
    health_diagnostic_repository = Mock()

    streaming_service = Mock()
    dashboard_service = Mock()
    dashboard_snapshot_service = Mock()
    dashboard_renderer = Mock()
    dashboard_application = Mock()

    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.get_settings",
                return_value=settings,
            )
        )

        http_client_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.HttpClient",
                side_effect=(
                    api_http_client,
                    metrics_http_client,
                ),
            )
        )

        mediamtx_client_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXClient",
                return_value=mediamtx_client,
            )
        )

        mediamtx_adapter_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXAdapter",
                return_value=mediamtx_adapter,
            )
        )

        geoip_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.GeoIPService",
                return_value=geoip_service,
            )
        )

        session_client_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXSessionClient",
                return_value=session_client,
            )
        )

        session_adapter_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXSessionAdapter",
                return_value=session_adapter,
            )
        )

        session_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SessionService",
                return_value=session_service,
            )
        )

        metrics_client_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXMetricsClient",
                return_value=metrics_client,
            )
        )

        metrics_parser_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXMetricsParser",
                return_value=metrics_parser,
            )
        )

        streaming_health_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.StreamingHealthService",
                return_value=streaming_health_service,
            )
        )

        system_adapter_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.LinuxSystemAdapter",
                return_value=system_adapter,
            )
        )

        system_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SystemService",
                return_value=system_service,
            )
        )

        network_telemetry_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NetworkTelemetryService",
                return_value=network_telemetry_service,
            )
        )

        node_id_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeId",
            )
        )
        node_id_class.create.return_value = node_id

        node_instance_id_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeInstanceId",
                return_value=node_instance_id,
            )
        )

        history_database_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteHistoryDatabase",
                return_value=history_database,
            )
        )

        event_history_repository_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteEventHistoryRepository",
                return_value=event_history_repository,
            )
        )

        alarm_history_repository_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteAlarmHistoryRepository",
                return_value=alarm_history_repository,
            )
        )

        history_query_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.HistoryQueryService",
                return_value=history_query_service,
            )
        )

        health_diagnostic_repository_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteNodeHealthDiagnosticRepository",
                return_value=health_diagnostic_repository,
            )
        )

        streaming_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.StreamingService",
                return_value=streaming_service,
            )
        )

        dashboard_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.DashboardService",
                return_value=dashboard_service,
            )
        )

        dashboard_snapshot_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.DashboardSnapshotService",
                return_value=dashboard_snapshot_service,
            )
        )

        dashboard_renderer_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.DashboardRenderer",
                return_value=dashboard_renderer,
            )
        )

        dashboard_application_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.DashboardApplication",
                return_value=dashboard_application,
            )
        )

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
    streaming_health_service_class.assert_called_once_with()

    system_adapter_class.assert_called_once_with()
    system_service_class.assert_called_once_with(
        system_adapter
    )
    network_telemetry_service_class.assert_called_once_with()

    node_id_class.create.assert_called_once_with(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
    )
    node_instance_id_class.assert_called_once_with(
        "streaming-primary"
    )

    history_database_class.assert_called_once_with(
        "/tmp/noc-history.db"
    )
    event_history_repository_class.assert_called_once_with(
        history_database
    )
    alarm_history_repository_class.assert_called_once_with(
        history_database
    )
    history_query_service_class.assert_called_once_with(
        event_repository=event_history_repository,
        alarm_repository=alarm_history_repository,
    )
    health_diagnostic_repository_class.assert_called_once_with(
        history_database
    )

    streaming_service_class.assert_called_once_with()
    dashboard_service_class.assert_called_once_with()
    dashboard_snapshot_service_class.assert_called_once_with(
        dashboard_service
    )
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
        dashboard_snapshot_service=dashboard_snapshot_service,
        health_diagnostic_repository=health_diagnostic_repository,
        history_query_service=history_query_service,
        node_id=node_id,
        instance_id=node_instance_id,
    )
