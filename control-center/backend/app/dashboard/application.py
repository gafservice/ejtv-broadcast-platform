"""Aplicación que coordina la ejecución del dashboard NOC."""

from __future__ import annotations

from time import sleep

from rich.layout import Layout
from rich.live import Live

from app.adapters.mediamtx.adapter import MediaMTXAdapter
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer
from app.dashboard.services.dashboard_service import DashboardService
from app.domain.streaming import MediaMTXSnapshot
from app.services.streaming_service import StreamingService
from app.services.system_service import SystemService


class DashboardApplication:
    """Coordina adquisición, medición, presentación y renderizado."""

    def __init__(
        self,
        *,
        mediamtx_adapter: MediaMTXAdapter,
        streaming_service: StreamingService,
        dashboard_service: DashboardService,
        dashboard_renderer: DashboardRenderer,
        system_service: SystemService,
    ) -> None:
        self._mediamtx_adapter = mediamtx_adapter
        self._streaming_service = streaming_service
        self._dashboard_service = dashboard_service
        self._dashboard_renderer = dashboard_renderer
        self._system_service = system_service

        self._previous_snapshot: MediaMTXSnapshot | None = None

    def run_once(self) -> Layout:
        """Obtiene una medición y renderiza una iteración del dashboard."""

        api_online = self._mediamtx_adapter.health()

        snapshot = self._mediamtx_adapter.get_snapshot()

        measurement = self._streaming_service.compare(
            self._previous_snapshot,
            snapshot,
        )

        system_info = self._system_service.get_system_info()

        dashboard_data = (
            self._dashboard_service.build_dashboard_from_measurement(
                hostname=system_info.hostname,
                mediamtx_online=api_online,
                api_online=api_online,
                snapshot=snapshot,
                measurement=measurement,
            )
        )

        rendered_dashboard = self._dashboard_renderer.render(
            dashboard_data
        )

        self._previous_snapshot = snapshot

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
