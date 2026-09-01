"""Pruebas del punto de entrada del monitor NOC."""

from contextlib import ExitStack
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
    settings.node_network_policy_path = (
        "/tmp/ejtv-01.yaml"
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

    repository = Mock()
    node_registry = Mock()

    history_database = Mock()
    event_history_repository = Mock()
    alarm_history_repository = Mock()
    alarm_recovery_service = Mock()
    history_query_service = Mock()

    bootstrap_result = Mock()
    bootstrap_result.node.node_id = Mock()

    node_instance_id = Mock()

    metric_service = Mock()
    node_health_service = Mock()

    network_policy = Mock()
    network_policy.interfaces = (
        Mock(),
    )

    policy_loader = Mock()
    policy_loader.load.return_value = network_policy

    session_policy = Mock()
    session_policy.expected_sessions = ()
    session_policy.critical_paths = ()
    session_policy.reconnect_flapping = None
    session_policy.has_reconnect_flapping = False

    session_policy_loader = Mock()
    session_policy_loader.load.return_value = (
        session_policy
    )

    reconnect_flapping_evaluator = Mock()

    expected_session_alarm_service = Mock()
    reconnect_flapping_alarm_service = Mock()
    critical_path_alarm_service = Mock()
    critical_path_unavailable_alarm_service = Mock()
    critical_path_traffic_stalled_alarm_service = Mock()

    session_alarm_runtime = Mock()
    session_operational_runtime = Mock()

    telemetry_refresh_service = Mock()

    streaming_service = Mock()
    dashboard_service = Mock()
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

        health_service_class = stack.enter_context(
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

        repository_class = stack.enter_context(
            patch(
                        "app.dashboard.live_monitor.InMemoryNodeRepository",
                        return_value=repository,
                    )
        )

        node_registry_class = stack.enter_context(
            patch(
                        "app.dashboard.live_monitor.NodeRegistry",
                        return_value=node_registry,
                    )
        )

        bootstrap_noc_runtime_mock = stack.enter_context(
            patch(
                        "app.dashboard.live_monitor.bootstrap_noc_runtime",
                        return_value=bootstrap_result,
                    )
        )

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

        alarm_recovery_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.AlarmRecoveryService",
                return_value=alarm_recovery_service,
            )
        )

        history_query_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.HistoryQueryService",
                return_value=history_query_service,
            )
        )

        metric_service_class = stack.enter_context(
            patch(
                        "app.dashboard.live_monitor.MetricService",
                        return_value=metric_service,
                    )
        )

        node_health_service_class = stack.enter_context(
            patch(
                        "app.dashboard.live_monitor.HealthService",
                        return_value=node_health_service,
                    )
        )

        event_service = object()
        event_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.EventService",
                return_value=event_service,
            )
        )

        health_transition_event_service = object()
        health_transition_event_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.HealthTransitionEventService",
                return_value=health_transition_event_service,
            )
        )

        session_transition_event_service = object()
        session_transition_event_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SessionTransitionEventService",
                return_value=session_transition_event_service,
            )
        )

        alarm_service = object()
        alarm_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.AlarmService",
                return_value=alarm_service,
            )
        )

        health_transition_alarm_service = object()
        health_transition_alarm_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.HealthTransitionAlarmService",
                return_value=health_transition_alarm_service,
            )
        )

        policy_loader_class = stack.enter_context(
            patch(
                        "app.dashboard.live_monitor.NodeNetworkPolicyLoader",
                        return_value=policy_loader,
                    )
        )

        session_policy_loader_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeSessionPolicyLoader",
                return_value=session_policy_loader,
            )
        )

        reconnect_flapping_evaluator_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.ReconnectFlappingEvaluator",
                return_value=reconnect_flapping_evaluator,
            )
        )

        expected_session_alarm_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.ExpectedSessionAlarmService",
                return_value=expected_session_alarm_service,
            )
        )

        reconnect_flapping_alarm_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.ReconnectFlappingAlarmService",
                return_value=reconnect_flapping_alarm_service,
            )
        )

        critical_path_alarm_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.CriticalPathNoReadersAlarmService",
                return_value=critical_path_alarm_service,
            )
        )

        critical_path_unavailable_alarm_service_class = (
            stack.enter_context(
                patch(
                    "app.dashboard.live_monitor."
                    "CriticalPathUnavailableAlarmService",
                    return_value=(
                        critical_path_unavailable_alarm_service
                    ),
                )
            )
        )

        critical_path_traffic_stalled_alarm_service_class = (
            stack.enter_context(
                patch(
                    "app.dashboard.live_monitor."
                    "CriticalPathTrafficStalledAlarmService",
                    return_value=(
                        critical_path_traffic_stalled_alarm_service
                    ),
                )
            )
        )

        session_alarm_runtime_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SessionAlarmRuntime",
                return_value=session_alarm_runtime,
            )
        )

        session_operational_runtime_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SessionOperationalRuntime",
                return_value=session_operational_runtime,
            )
        )

        telemetry_refresh_service_class = stack.enter_context(
            patch(
                        "app.dashboard.live_monitor.TelemetryRefreshService",
                        return_value=telemetry_refresh_service,
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
    health_service_class.assert_called_once_with()

    system_adapter_class.assert_called_once_with()

    system_service_class.assert_called_once_with(
        system_adapter
    )

    repository_class.assert_called_once_with()

    node_registry_class.assert_called_once_with(
        repository
    )

    bootstrap_noc_runtime_mock.assert_called_once_with(
        node_registry
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

    metric_service_class.assert_called_once_with(
        node_registry
    )

    node_health_service_class.assert_called_once_with(
        node_registry
    )

    event_service_class.assert_called_once_with(
        node_registry,
        history_repository=event_history_repository,
    )

    health_transition_event_service_class.assert_called_once_with(
        event_service=event_service,
    )

    session_transition_event_service_class.assert_called_once_with(
        event_service=event_service,
    )

    alarm_service_class.assert_called_once_with(
        node_registry,
        history_repository=alarm_history_repository,
    )

    alarm_recovery_service_class.assert_called_once_with(
        registry=node_registry,
        history_repository=alarm_history_repository,
    )

    alarm_recovery_service.recover.assert_called_once_with(
        node_id=bootstrap_result.node.node_id,
        instance_id=node_instance_id,
    )

    health_transition_alarm_service_class.assert_called_once_with(
        alarm_service=alarm_service,
    )

    policy_loader_class.assert_called_once_with()

    policy_loader.load.assert_called_once_with(
        "/tmp/ejtv-01.yaml"
    )

    session_policy_loader_class.assert_called_once_with()

    session_policy_loader.load.assert_called_once_with(
        "/tmp/ejtv-01.yaml"
    )

    reconnect_flapping_evaluator_class.assert_called_once_with()

    expected_session_alarm_service_class.assert_called_once_with(
        alarm_service=alarm_service,
    )

    reconnect_flapping_alarm_service_class.assert_called_once_with(
        alarm_service=alarm_service,
    )

    critical_path_alarm_service_class.assert_called_once_with(
        alarm_service=alarm_service,
    )

    critical_path_unavailable_alarm_service_class.assert_called_once_with(
        alarm_service=alarm_service,
    )

    critical_path_traffic_stalled_alarm_service_class.assert_called_once_with(
        alarm_service=alarm_service,
    )

    session_alarm_runtime_class.assert_called_once_with(
        expected_session_alarm_service=(
            expected_session_alarm_service
        ),
        reconnect_flapping_alarm_service=(
            reconnect_flapping_alarm_service
        ),
        critical_path_alarm_service=(
            critical_path_alarm_service
        ),
        critical_path_unavailable_alarm_service=(
            critical_path_unavailable_alarm_service
        ),
        critical_path_traffic_stalled_alarm_service=(
            critical_path_traffic_stalled_alarm_service
        ),
        expected_session_policies=(
            session_policy.expected_sessions
        ),
        critical_path_policies=(
            session_policy.critical_paths
        ),
        reconnect_flapping_evaluator=(
            reconnect_flapping_evaluator
        ),
        reconnect_flapping_enabled=(
            session_policy.has_reconnect_flapping
        ),
    )

    session_operational_runtime_class.assert_called_once_with(
        transition_event_service=(
            session_transition_event_service
        ),
        alarm_runtime=session_alarm_runtime,
    )

    telemetry_refresh_service_class.assert_called_once_with(
        system_service=system_service,
        metric_service=metric_service,
        health_service=node_health_service,
        health_transition_event_service=(
            health_transition_event_service
        ),
        health_transition_alarm_service=(
            health_transition_alarm_service
        ),
        network_policies=network_policy.interfaces,
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
        telemetry_refresh_service=telemetry_refresh_service,
        session_transition_event_service=(
            session_transition_event_service
        ),
        session_operational_runtime=(
            session_operational_runtime
        ),
        event_service=event_service,
        alarm_service=alarm_service,
        node_id=bootstrap_result.node.node_id,
        instance_id=node_instance_id,
    )
