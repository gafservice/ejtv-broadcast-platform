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

    settings.stream_health_srt_degradation_seconds = 7.5
    settings.stream_health_srt_recovery_seconds = 12.0

    settings.geoip_database_path = (
        "data/geoip/GeoLite2-Country.mmdb"
    )
    settings.noc_history_database_path = (
        "/tmp/noc-history.db"
    )
    settings.noc_evidence_path = (
        "/tmp/noc-evidence"
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
    streaming_health_aggregator = Mock()
    srt_connection_health_stabilizer = Mock()
    streaming_health_stabilizer = Mock()

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

        streaming_health_aggregator_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.StreamingHealthAggregator",
                return_value=streaming_health_aggregator,
            )
        )

        srt_connection_health_stabilizer_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SRTConnectionHealthStabilizer",
                return_value=srt_connection_health_stabilizer,
            )
        )

        streaming_health_stabilizer_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.StreamingHealthStabilizer",
                return_value=streaming_health_stabilizer,
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

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.InMemoryNodeRepository",
            )
        )
        node_registry_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeRegistry",
            )
        )
        node_registry = node_registry_class.return_value

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.bootstrap_noc_runtime",
            )
        )
        evidence_writer_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.JsonlEvidenceWriter",
            )
        )
        evidence_writer = evidence_writer_class.return_value
        event_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.EventService",
            )
        )
        event_service = event_service_class.return_value

        alarm_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.AlarmService",
            )
        )
        alarm_service = alarm_service_class.return_value

        stream_alarm_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "StreamingHealthTransitionAlarmService",
            )
        )
        stream_alarm_service = (
            stream_alarm_service_class.return_value
        )

        transition_detector_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "StreamingHealthTransitionDetector",
            )
        )
        transition_detector = (
            transition_detector_class.return_value
        )

        stream_event_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "StreamingHealthTransitionEventService",
            )
        )
        stream_event_service = (
            stream_event_service_class.return_value
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
    streaming_health_aggregator_class.assert_called_once_with()

    srt_connection_health_stabilizer_class.assert_called_once_with(
        degradation_seconds=7.5,
        recovery_seconds=12.0,
    )
    streaming_health_stabilizer_class.assert_called_once_with(
        connection_stabilizer=srt_connection_health_stabilizer,
    )

    transition_detector_class.assert_called_once_with()

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

    alarm_service_class.assert_called_once_with(
        node_registry,
        history_repository=alarm_history_repository,
        evidence_writer=evidence_writer,
    )

    stream_alarm_service_class.assert_called_once_with(
        alarm_service=alarm_service
    )

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
        streaming_health_aggregator=streaming_health_aggregator,
        streaming_health_stabilizer=streaming_health_stabilizer,
        streaming_health_transition_detector=transition_detector,
        dashboard_snapshot_service=dashboard_snapshot_service,
        health_diagnostic_repository=health_diagnostic_repository,
        streaming_health_transition_event_service=(
            stream_event_service
        ),
        streaming_health_transition_alarm_service=(
            stream_alarm_service
        ),
        history_query_service=history_query_service,
        node_id=node_id,
        instance_id=node_instance_id,
    )


def test_build_dashboard_application_disables_temporal_health_without_policy() -> None:
    """Sin política temporal, el monitor conserva Health instantáneo."""

    settings = Mock()
    settings.mediamtx_api_url = "http://127.0.0.1:9997"
    settings.mediamtx_api_timeout_seconds = 3.0
    settings.mediamtx_metrics_url = "http://127.0.0.1:9998"
    settings.mediamtx_metrics_timeout_seconds = 4.0

    settings.stream_health_srt_degradation_seconds = None
    settings.stream_health_srt_recovery_seconds = None

    settings.geoip_database_path = (
        "data/geoip/GeoLite2-Country.mmdb"
    )
    settings.noc_history_database_path = (
        "/tmp/noc-history.db"
    )
    settings.noc_evidence_path = (
        "/tmp/noc-evidence"
    )

    dashboard_application = Mock()

    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.get_settings",
                return_value=settings,
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.HttpClient",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXClient",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXAdapter",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.GeoIPService",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXSessionClient",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXSessionAdapter",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SessionService",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXMetricsClient",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXMetricsParser",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.StreamingHealthService",
            )
        )

        srt_connection_health_stabilizer_class = (
            stack.enter_context(
                patch(
                    "app.dashboard.live_monitor."
                    "SRTConnectionHealthStabilizer",
                )
            )
        )

        streaming_health_stabilizer_class = (
            stack.enter_context(
                patch(
                    "app.dashboard.live_monitor."
                    "StreamingHealthStabilizer",
                )
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.LinuxSystemAdapter",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SystemService",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NetworkTelemetryService",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeId",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeInstanceId",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteHistoryDatabase",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "SQLiteEventHistoryRepository",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "SQLiteAlarmHistoryRepository",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.HistoryQueryService",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "SQLiteNodeHealthDiagnosticRepository",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.StreamingService",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.DashboardService",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.DashboardSnapshotService",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.DashboardRenderer",
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.InMemoryNodeRepository",
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeRegistry",
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.bootstrap_noc_runtime",
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.JsonlEvidenceWriter",
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.EventService",
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.AlarmService",
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "StreamingHealthTransitionAlarmService",
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "StreamingHealthTransitionEventService",
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

    srt_connection_health_stabilizer_class.assert_not_called()
    streaming_health_stabilizer_class.assert_not_called()

    dashboard_application_class.assert_called_once()

    _, kwargs = dashboard_application_class.call_args

    assert kwargs["streaming_health_stabilizer"] is None


def test_build_dashboard_application_composes_stream_health_event_runtime() -> None:
    """Block 4 debe conectar Stream Health Events al runtime real del terminal."""

    settings = Mock()
    settings.mediamtx_api_url = "http://127.0.0.1:9997"
    settings.mediamtx_api_timeout_seconds = 3.0
    settings.mediamtx_metrics_url = "http://127.0.0.1:9998"
    settings.mediamtx_metrics_timeout_seconds = 4.0

    settings.stream_health_srt_degradation_seconds = None
    settings.stream_health_srt_recovery_seconds = None

    settings.geoip_database_path = (
        "data/geoip/GeoLite2-Country.mmdb"
    )
    settings.noc_history_database_path = (
        "/tmp/block4-noc-history.db"
    )
    settings.noc_evidence_path = (
        "/tmp/block4-noc-evidence"
    )

    dashboard_application = Mock()

    node_repository = Mock()
    node_registry = Mock()
    bootstrap_result = Mock()

    evidence_writer = Mock()
    event_service = Mock()
    stream_event_service = Mock()

    event_history_repository = Mock()

    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.get_settings",
                return_value=settings,
            )
        )

        # Existing unrelated composition is isolated.
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.HttpClient"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXClient"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXAdapter"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.GeoIPService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXSessionClient"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.MediaMTXSessionAdapter"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SessionService"
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
                "app.dashboard.live_monitor.StreamingHealthService"
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
                "app.dashboard.live_monitor.NetworkTelemetryService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeId"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeInstanceId"
            )
        )

        history_database_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteHistoryDatabase"
            )
        )

        history_database = Mock()
        history_database_class.return_value = history_database

        event_history_repository_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteEventHistoryRepository",
                return_value=event_history_repository,
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteAlarmHistoryRepository"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.HistoryQueryService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.SQLiteNodeHealthDiagnosticRepository"
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.StreamingService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.DashboardService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.DashboardSnapshotService"
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.DashboardRenderer"
            )
        )

        node_repository_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.InMemoryNodeRepository",
                return_value=node_repository,
            )
        )

        node_registry_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.NodeRegistry",
                return_value=node_registry,
            )
        )

        bootstrap = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.bootstrap_noc_runtime",
                return_value=bootstrap_result,
            )
        )

        evidence_writer_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.JsonlEvidenceWriter",
                return_value=evidence_writer,
            )
        )

        event_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.EventService",
                return_value=event_service,
            )
        )

        stack.enter_context(
            patch(
                "app.dashboard.live_monitor.AlarmService",
            )
        )
        stack.enter_context(
            patch(
                "app.dashboard.live_monitor."
                "StreamingHealthTransitionAlarmService",
            )
        )

        stream_event_service_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.StreamingHealthTransitionEventService",
                return_value=stream_event_service,
            )
        )

        transition_detector_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.StreamingHealthTransitionDetector"
            )
        )
        transition_detector = transition_detector_class.return_value

        dashboard_application_class = stack.enter_context(
            patch(
                "app.dashboard.live_monitor.DashboardApplication",
                return_value=dashboard_application,
            )
        )

        result = build_dashboard_application()

    assert result is dashboard_application

    node_repository_class.assert_called_once_with()
    node_registry_class.assert_called_once_with(
        node_repository
    )
    bootstrap.assert_called_once_with(
        node_registry
    )

    evidence_writer_class.assert_called_once_with(
        "/tmp/block4-noc-evidence"
    )

    event_history_repository_class.assert_called_once_with(
        history_database
    )

    event_service_class.assert_called_once_with(
        node_registry,
        history_repository=event_history_repository,
        evidence_writer=evidence_writer,
    )

    stream_event_service_class.assert_called_once_with(
        event_service=event_service
    )

    transition_detector_class.assert_called_once_with()

    _, kwargs = dashboard_application_class.call_args

    assert (
        kwargs["streaming_health_transition_detector"]
        is transition_detector
    )

    assert (
        kwargs["streaming_health_transition_event_service"]
        is stream_event_service
    )
