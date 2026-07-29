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
from app.services.session_service import SessionService
from app.services.streaming_health_service import StreamingHealthService
from app.services.streaming_service import StreamingService
from app.services.system_service import SystemService
from app.services.geoip_service import GeoIPService


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