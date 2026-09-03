"""Punto de entrada del monitor NOC."""

from __future__ import annotations

from app.adapters.linux.linux_system_adapter import LinuxSystemAdapter
from app.adapters.mediamtx.adapter import MediaMTXAdapter
from app.adapters.mediamtx.client import MediaMTXClient
from app.adapters.mediamtx.metrics_client import MediaMTXMetricsClient
from app.adapters.mediamtx.metrics_parser import MediaMTXMetricsParser
from app.adapters.mediamtx.session_adapter import MediaMTXSessionAdapter
from app.adapters.mediamtx.session_client import MediaMTXSessionClient
from app.core.config import get_settings
from app.core.http import HttpClient
from app.dashboard.application import DashboardApplication
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer
from app.dashboard.services.dashboard_service import DashboardService
from app.dashboard.services.dashboard_snapshot_service import (
    DashboardSnapshotService,
)
from app.services.network_telemetry_service import (
    NetworkTelemetryService,
)
from app.services.session_service import SessionService
from app.services.streaming_health_service import StreamingHealthService
from app.services.streaming_service import StreamingService
from app.services.system_service import SystemService
from app.services.geoip_service import GeoIPService

from app.noc.bootstrap import (
    DEFAULT_INSTANCE_ID,
    DEFAULT_NODE_DISPLAY_NAME,
    DEFAULT_NODE_ID,
    DEFAULT_NODE_NAME,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.sqlite_alarm_repository import (
    SQLiteAlarmHistoryRepository,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)
from app.noc.history.sqlite_event_repository import (
    SQLiteEventHistoryRepository,
)
from app.noc.current_state.sqlite_node_health_diagnostic_repository import (
    SQLiteNodeHealthDiagnosticRepository,
)
from app.noc.services.history_query_service import (
    HistoryQueryService,
)


def build_dashboard_application() -> DashboardApplication:
    """Construye el runtime completo del monitor NOC."""

    settings = get_settings()

    api_http_client = HttpClient(
        base_url=settings.mediamtx_api_url,
        timeout=settings.mediamtx_api_timeout_seconds,
    )

    #
    # Streaming
    #
    mediamtx_client = MediaMTXClient(api_http_client)
    mediamtx_adapter = MediaMTXAdapter(mediamtx_client)

    #
    # Active Sessions
    #
    geoip_service = GeoIPService(
        settings.geoip_database_path
    )

    session_client = MediaMTXSessionClient(api_http_client)
    session_adapter = MediaMTXSessionAdapter(
        session_client,
        geoip_service,
    )
    session_service = SessionService()

    #
    # Prometheus Metrics
    #
    metrics_http_client = HttpClient(
        base_url=settings.mediamtx_metrics_url,
        timeout=settings.mediamtx_metrics_timeout_seconds,
        default_headers={
            "Accept": "text/plain",
        },
    )

    metrics_client = MediaMTXMetricsClient(
        metrics_http_client
    )

    metrics_parser = MediaMTXMetricsParser()
    streaming_health_service = StreamingHealthService()

    #
    # System
    #
    system_adapter = LinuxSystemAdapter()
    system_service = SystemService(system_adapter)
    network_telemetry_service = NetworkTelemetryService()

    #
    # Shared NOC Read Model
    #

    node_id = NodeId.create(
        id=DEFAULT_NODE_ID,
        name=DEFAULT_NODE_NAME,
        display_name=DEFAULT_NODE_DISPLAY_NAME,
    )

    node_instance_id = NodeInstanceId(
        DEFAULT_INSTANCE_ID
    )

    history_database = SQLiteHistoryDatabase(
        settings.noc_history_database_path
    )

    event_history_repository = (
        SQLiteEventHistoryRepository(
            history_database
        )
    )

    alarm_history_repository = (
        SQLiteAlarmHistoryRepository(
            history_database
        )
    )

    history_query_service = HistoryQueryService(
        event_repository=event_history_repository,
        alarm_repository=alarm_history_repository,
    )

    health_diagnostic_repository = (
        SQLiteNodeHealthDiagnosticRepository(
            history_database
        )
    )

    #
    # Dashboard
    #
    streaming_service = StreamingService()
    dashboard_service = DashboardService()
    dashboard_snapshot_service = DashboardSnapshotService(
        dashboard_service
    )
    dashboard_renderer = DashboardRenderer()

    return DashboardApplication(
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


def main() -> None:
    """Inicia el monitor NOC conectado a MediaMTX."""

    application = build_dashboard_application()

    try:
        application.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
