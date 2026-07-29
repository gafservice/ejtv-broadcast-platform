"""Aplicación que coordina la ejecución del dashboard NOC."""

from __future__ import annotations

from datetime import datetime
from time import sleep


from rich.layout import Layout
from rich.live import Live

from app.adapters.mediamtx.adapter import MediaMTXAdapter
from app.adapters.mediamtx.metrics_client import MediaMTXMetricsClient
from app.adapters.mediamtx.metrics_parser import MediaMTXMetricsParser
from app.adapters.mediamtx.session_adapter import MediaMTXSessionAdapter
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer
from app.dashboard.models import DashboardData
from app.dashboard.services.dashboard_service import DashboardService
from app.dashboard.services.dashboard_snapshot_service import (
    DashboardSnapshotInput,
    DashboardSnapshotService,
)
from app.domain.sessions import SessionSnapshot
from app.domain.streaming import MediaMTXSnapshot, StreamingHealth
from app.domain.system import SystemResources
from app.services.session_service import SessionService
from app.services.streaming_health_service import StreamingHealthService
from app.services.streaming_service import StreamingService
from app.services.system_service import SystemService


class DashboardApplication:
    """Coordina adquisición, medición, salud y renderizado."""

    def __init__(
        self,
        *,
        mediamtx_adapter: MediaMTXAdapter,
        session_adapter: MediaMTXSessionAdapter,
        streaming_service: StreamingService,
        session_service: SessionService,
        dashboard_service: DashboardService,
        dashboard_renderer: DashboardRenderer,
        system_service: SystemService,
        metrics_client: MediaMTXMetricsClient | None = None,
        metrics_parser: MediaMTXMetricsParser | None = None,
        streaming_health_service: StreamingHealthService | None = None,
        dashboard_snapshot_service: DashboardSnapshotService | None = None,
    ) -> None:
        self._mediamtx_adapter = mediamtx_adapter
        self._session_adapter = session_adapter

        self._streaming_service = streaming_service
        self._session_service = session_service

        self._dashboard_service = dashboard_service
        self._dashboard_snapshot_service = (
            dashboard_snapshot_service
            if dashboard_snapshot_service is not None
            else DashboardSnapshotService(dashboard_service)
        )
        self._dashboard_renderer = dashboard_renderer
        self._system_service = system_service

        self._metrics_client = metrics_client
        self._metrics_parser = metrics_parser
        self._streaming_health_service = streaming_health_service

        self._previous_snapshot: MediaMTXSnapshot | None = None
        self._previous_session_snapshot: SessionSnapshot | None = None
        self._previous_system_resources: SystemResources | None = None
        self._latest_health: StreamingHealth | None = None

        self._validate_health_dependencies()

    @property
    def latest_health(self) -> StreamingHealth | None:
        """Último estado de salud calculado por la aplicación."""

        return self._latest_health

    def build_dashboard(self) -> DashboardData:
        """Construye el estado completo del dashboard sin renderizar."""

        api_online = self._mediamtx_adapter.health()

        snapshot = self._mediamtx_adapter.get_snapshot()

        session_snapshot = self._session_adapter.get_snapshot()

        measurement = self._streaming_service.compare(
            self._previous_snapshot,
            snapshot,
        )

        session_measurement = self._session_service.measure(
            session_snapshot,
        )

        streaming_health = self._build_streaming_health(
            captured_at=snapshot.captured_at,
        )

        system_info = self._system_service.get_system_info()
        system_resources = self._system_service.get_system_resources()

        snapshot_kwargs = {
            "hostname": system_info.hostname,
            "mediamtx_online": api_online,
            "api_online": api_online,
            "snapshot": snapshot,
            "measurement": measurement,
            "session_measurement": session_measurement,
            "system_resources": system_resources,
            "previous_system_resources": self._previous_system_resources,
        }

        if streaming_health is not None:
            snapshot_kwargs["health"] = streaming_health

        snapshot_input = DashboardSnapshotInput(**snapshot_kwargs)

        dashboard_data = self._dashboard_snapshot_service.build_snapshot(
            snapshot_input
        )

        self._previous_snapshot = snapshot
        self._previous_session_snapshot = session_snapshot
        self._previous_system_resources = system_resources
        self._latest_health = streaming_health

        return dashboard_data


    def run_once(self) -> Layout:
        """Obtiene una medición y renderiza una iteración del dashboard."""

        dashboard_data = self.build_dashboard()

        return self._dashboard_renderer.render(
            dashboard_data
    )

    def run(
        self,
        *,
        refresh_interval_seconds: float = 1.0,
        max_iterations: int | None = None,
    ) -> None:
        """Ejecuta continuamente el dashboard utilizando Rich Live."""

        iteration = 0

        with Live(
            screen=True,
            auto_refresh=False,
        ) as live:

            while (
                max_iterations is None
                or iteration < max_iterations
            ):
                rendered_dashboard = self.run_once()

                live.update(
                    rendered_dashboard,
                    refresh=True,
                )

                iteration += 1

                if (
                    max_iterations is not None
                    and iteration >= max_iterations
                ):
                    break

                sleep(refresh_interval_seconds)

    def _build_streaming_health(
    self,
    *,
    captured_at: datetime,
    ) -> StreamingHealth | None:
        """Obtiene y transforma las métricas Prometheus disponibles."""

        if self._metrics_client is None:
            return None

        if self._metrics_parser is None:
            return None

        if self._streaming_health_service is None:
            return None

        metrics_text = self._metrics_client.get_metrics_text()

        metrics_snapshot = self._metrics_parser.parse(
            metrics_text
        )

        return self._streaming_health_service.build(
            snapshot=metrics_snapshot,
            captured_at=captured_at,
        )

    def _validate_health_dependencies(self) -> None:
        """Evita una configuración parcial del motor de salud."""

        dependencies = (
            self._metrics_client,
            self._metrics_parser,
            self._streaming_health_service,
        )

        configured_count = sum(
            dependency is not None
            for dependency in dependencies
        )

        if configured_count not in (0, len(dependencies)):
            raise ValueError(
                "metrics_client, metrics_parser y "
                "streaming_health_service deben configurarse juntos."
            )