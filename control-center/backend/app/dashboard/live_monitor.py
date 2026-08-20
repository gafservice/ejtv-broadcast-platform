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
    bootstrap_noc_runtime,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.infrastructure.memory_repository import (
    InMemoryNodeRepository,
)
from app.noc.infrastructure.node_network_policy_loader import (
    NodeNetworkPolicyLoader,
)
from app.noc.registry.registry import NodeRegistry
from app.noc.runtime.telemetry_refresh import (
    TelemetryRefreshService,
)
from app.noc.services.event_service import EventService
from app.noc.services.health_service import HealthService
from app.noc.services.health_transition_event_service import (
    HealthTransitionEventService,
)
from app.noc.services.metric_service import MetricService


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
    # NOC Node Runtime
    #
    node_registry = NodeRegistry(
        InMemoryNodeRepository()
    )

    bootstrap_result = bootstrap_noc_runtime(
        node_registry
    )

    node_instance_id = NodeInstanceId(
        DEFAULT_INSTANCE_ID
    )

    metric_service = MetricService(
        node_registry
    )

    node_health_service = HealthService(
        node_registry
    )

    event_service = EventService(
        node_registry
    )

    health_transition_event_service = (
        HealthTransitionEventService(
            event_service=event_service,
        )
    )

    network_policy = (
        NodeNetworkPolicyLoader().load(
            settings.node_network_policy_path
        )
    )

    telemetry_refresh_service = (
        TelemetryRefreshService(
            system_service=system_service,
            metric_service=metric_service,
            health_service=node_health_service,
            health_transition_event_service=(
                health_transition_event_service
            ),
            network_policies=network_policy.interfaces,
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
        telemetry_refresh_service=telemetry_refresh_service,
        node_id=bootstrap_result.node.node_id,
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
