"""Aplicación que coordina la ejecución del dashboard NOC."""

from __future__ import annotations

from time import sleep
from typing import Any

from rich.layout import Layout
from rich.live import Live

from app.adapters.mediamtx.adapter import MediaMTXAdapter
from app.adapters.mediamtx.metrics_client import MediaMTXMetricsClient
from app.adapters.mediamtx.metrics_parser import MediaMTXMetricsParser
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer
from app.dashboard.services.dashboard_service import DashboardService
from app.domain.streaming import MediaMTXSnapshot, StreamingHealth
from app.domain.system import SystemResources
from app.services.streaming_health_service import StreamingHealthService
from app.services.streaming_service import StreamingService
from app.services.system_service import SystemService


class DashboardApplication:
    """Coordina adquisición, medición, salud y renderizado."""

    def __init__(
        self,
        *,
        mediamtx_adapter: MediaMTXAdapter,
        streaming_service: StreamingService,
        dashboard_service: DashboardService,
        dashboard_renderer: DashboardRenderer,
        system_service: SystemService,
        metrics_client: MediaMTXMetricsClient | None = None,
        metrics_parser: MediaMTXMetricsParser | None = None,
        streaming_health_service: StreamingHealthService | None = None,
    ) -> None:
        self._mediamtx_adapter = mediamtx_adapter
        self._streaming_service = streaming_service
        self._dashboard_service = dashboard_service
        self._dashboard_renderer = dashboard_renderer
        self._system_service = system_service

        self._metrics_client = metrics_client
        self._metrics_parser = metrics_parser
        self._streaming_health_service = streaming_health_service

        self._previous_snapshot: MediaMTXSnapshot | None = None
        self._previous_system_resources: SystemResources | None = None
        self._latest_health: StreamingHealth | None = None

        self._validate_health_dependencies()

    @property
    def latest_health(self) -> StreamingHealth | None:
        """Último estado de salud calculado por la aplicación."""

        return self._latest_health

    def run_once(self) -> Layout:
        """Obtiene una medición y renderiza una iteración del dashboard."""

        api_online = self._mediamtx_adapter.health()

        snapshot = self._mediamtx_adapter.get_snapshot()

        measurement = self._streaming_service.compare(
            self._previous_snapshot,
            snapshot,
        )

        streaming_health = self._build_streaming_health(
            captured_at=snapshot.captured_at,
        )

        system_info = self._system_service.get_system_info()
        system_resources = self._system_service.get_system_resources()

        dashboard_arguments: dict[str, Any] = {
            "hostname": system_info.hostname,
            "mediamtx_online": api_online,
            "api_online": api_online,
            "snapshot": snapshot,
            "measurement": measurement,
            "system_resources": system_resources,
            "previous_system_resources": (
                self._previous_system_resources
            ),
        }

        if streaming_health is not None:
            dashboard_arguments["health"] = streaming_health

        dashboard_data = (
            self._dashboard_service.build_dashboard_from_measurement(
                **dashboard_arguments
            )
        )

        rendered_dashboard = self._dashboard_renderer.render(
            dashboard_data
        )

        self._previous_snapshot = snapshot
        self._previous_system_resources = system_resources
        self._latest_health = streaming_health

        return rendered_dashboard

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
        captured_at: Any,
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
