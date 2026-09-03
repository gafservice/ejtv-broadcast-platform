"""Aplicación que coordina la ejecución del dashboard NOC."""

from __future__ import annotations

from contextlib import ExitStack
from datetime import datetime
from time import monotonic, sleep


from rich.layout import Layout
from rich.live import Live

from app.adapters.mediamtx.adapter import MediaMTXAdapter
from app.adapters.mediamtx.metrics_client import MediaMTXMetricsClient
from app.adapters.mediamtx.metrics_parser import MediaMTXMetricsParser
from app.adapters.mediamtx.session_adapter import MediaMTXSessionAdapter
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer
from app.dashboard.models.dashboard_navigation_action import (
    DashboardNavigationAction,
)
from app.dashboard.models.dashboard_navigation_state import (
    DashboardNavigationState,
)
from app.dashboard.models.dashboard_navigation_totals import (
    DashboardNavigationTotals,
)
from app.dashboard.models import DashboardData
from app.dashboard.services.dashboard_navigation_controller import (
    DashboardNavigationController,
)
from app.dashboard.services.dashboard_key_parser import (
    DashboardKeyParser,
)
from app.dashboard.services.posix_keyboard_input import (
    PosixKeyboardInput,
)
from app.dashboard.services.dashboard_service import DashboardService
from app.dashboard.services.dashboard_snapshot_service import (
    DashboardSnapshotInput,
    DashboardSnapshotService,
)
from app.domain.sessions import SessionSnapshot
from app.domain.streaming import MediaMTXSnapshot, StreamingHealth
from app.domain.system import SystemResources
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.telemetry_refresh import (
    TelemetryRefreshService,
)
from app.noc.runtime.session_operational_runtime import (
    SessionOperationalRuntime,
)
from app.noc.services.alarm_service import AlarmService
from app.noc.services.event_service import EventService
from app.noc.services.history_query_service import HistoryQueryService
from app.services.network_telemetry_service import (
    NetworkTelemetryService,
)
from app.services.session_service import SessionService
from app.services.streaming_health_service import StreamingHealthService
from app.services.streaming_service import StreamingService
from app.services.system_service import SystemService
from app.noc.services.session_transition_event_service import (
    SessionTransitionEventService,
)


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
        network_telemetry_service: NetworkTelemetryService | None = None,
        telemetry_refresh_service: TelemetryRefreshService | None = None,
        session_transition_event_service: (
            SessionTransitionEventService | None
        ) = None,
        session_operational_runtime: (
            SessionOperationalRuntime | None
        ) = None,
        event_service: EventService | None = None,
        alarm_service: AlarmService | None = None,
        history_query_service: HistoryQueryService | None = None,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
        navigation_state: DashboardNavigationState | None = None,
        navigation_controller: DashboardNavigationController | None = None,
        key_parser: DashboardKeyParser | None = None,
        keyboard_input: PosixKeyboardInput | None = None,
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
        self._network_telemetry_service = (
            network_telemetry_service
            if network_telemetry_service is not None
            else NetworkTelemetryService()
        )

        self._metrics_client = metrics_client
        self._metrics_parser = metrics_parser
        self._streaming_health_service = streaming_health_service

        self._telemetry_refresh_service = telemetry_refresh_service
        self._session_transition_event_service = (
            session_transition_event_service
        )
        self._session_operational_runtime = (
            session_operational_runtime
        )
        self._event_service = event_service
        self._alarm_service = alarm_service
        self._history_query_service = history_query_service
        self._node_id = node_id
        self._instance_id = instance_id

        self._navigation_state = (
            navigation_state
            if navigation_state is not None
            else DashboardNavigationState()
        )

        self._navigation_totals = DashboardNavigationTotals()

        self._navigation_controller = (
            navigation_controller
            if navigation_controller is not None
            else DashboardNavigationController()
        )

        self._key_parser = (
            key_parser
            if key_parser is not None
            else DashboardKeyParser()
        )

        self._keyboard_input = (
            keyboard_input
            if keyboard_input is not None
            else PosixKeyboardInput()
        )

        self._previous_snapshot: MediaMTXSnapshot | None = None
        self._previous_session_snapshot: SessionSnapshot | None = None
        self._previous_system_resources: SystemResources | None = None
        self._latest_health: StreamingHealth | None = None

        self._validate_health_dependencies()
        self._validate_noc_dependencies()

    @property
    def navigation_state(self) -> DashboardNavigationState:
        """Estado interactivo actual del dashboard."""

        return self._navigation_state

    @property
    def navigation_totals(self) -> DashboardNavigationTotals:
        """Totales navegables de la última captura."""

        return self._navigation_totals

    def set_navigation_state(
        self,
        state: DashboardNavigationState,
    ) -> None:
        """Reemplaza el estado interactivo del dashboard."""

        if not isinstance(
            state,
            DashboardNavigationState,
        ):
            raise TypeError(
                "state must be a DashboardNavigationState"
            )

        self._navigation_state = state

    def apply_navigation_action(
        self,
        action: DashboardNavigationAction,
    ) -> None:
        """Aplica una acción sobre el panel actualmente seleccionado."""

        if not isinstance(
            action,
            DashboardNavigationAction,
        ):
            raise TypeError(
                "action must be a DashboardNavigationAction"
            )

        total_items = self._navigation_totals.for_panel(
            self._navigation_state.active_panel
        )

        self._navigation_state = self._navigation_controller.apply(
            self._navigation_state,
            action,
            total_items=total_items,
        )

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

        interface_infos = (
            self._system_service.get_network_interface_infos()
        )

        network_telemetry = (
            self._network_telemetry_service.build(
                previous=self._previous_system_resources,
                current=system_resources,
                interface_infos=interface_infos,
            )
        )

        network_interfaces = (
            self._dashboard_service.build_network_interfaces_panel(
                telemetry=network_telemetry,
            )
        )

        node_health = None
        recent_events = None
        active_alarms = None

        if self._telemetry_refresh_service is not None:
            if self._session_operational_runtime is not None:
                self._session_operational_runtime.process(
                    node_id=self._node_id,
                    instance_id=self._instance_id,
                    previous=self._previous_session_snapshot,
                    current=session_snapshot,
                    media_snapshot=snapshot,
                    streaming_measurement=measurement,
                    timestamp=session_snapshot.captured_at,
                )
            elif self._session_transition_event_service is not None:
                self._session_transition_event_service.process(
                    node_id=self._node_id,
                    instance_id=self._instance_id,
                    previous=self._previous_session_snapshot,
                    current=session_snapshot,
                    timestamp=session_snapshot.captured_at,
                )

            telemetry_result = (
                self._telemetry_refresh_service.refresh_from_capture(
                    node_id=self._node_id,
                    instance_id=self._instance_id,
                    resources=system_resources,
                    interface_infos=interface_infos,
                )
            )

            node_health = (
                self._dashboard_service.build_node_health_panel(
                    diagnostic=telemetry_result.health_diagnostic,
                )
            )

            event_history_records = (
                self._history_query_service.recent_events(
                    node_id=self._node_id,
                    instance_id=self._instance_id,
                )
            )

            event_records = tuple(
                record.event
                for record in event_history_records
            )

            recent_events = (
                self._dashboard_service.build_recent_events_panel(
                    events=event_records,
                    viewport=self._navigation_state.recent_events,
                )
            )

            alarm_records = (
                self._history_query_service.active_alarms(
                    node_id=self._node_id,
                    instance_id=self._instance_id,
                )
            )

            active_alarms = (
                self._dashboard_service.build_active_alarms_panel(
                    alarms=alarm_records,
                    viewport=self._navigation_state.active_alarms,
                )
            )

        snapshot_kwargs = {
            "hostname": system_info.hostname,
            "mediamtx_online": api_online,
            "api_online": api_online,
            "snapshot": snapshot,
            "measurement": measurement,
            "session_measurement": session_measurement,
            "active_connections_viewport": (
                self._navigation_state.active_connections
            ),
            "system_resources": system_resources,
            "previous_system_resources": self._previous_system_resources,
            "network_interfaces": network_interfaces,
        }

        if streaming_health is not None:
            snapshot_kwargs["health"] = streaming_health

        if node_health is not None:
            snapshot_kwargs["node_health"] = node_health

        if recent_events is not None:
            snapshot_kwargs["recent_events"] = recent_events

        if active_alarms is not None:
            snapshot_kwargs["active_alarms"] = active_alarms

        snapshot_input = DashboardSnapshotInput(**snapshot_kwargs)

        dashboard_data = self._dashboard_snapshot_service.build_snapshot(
            snapshot_input
        )

        self._navigation_totals = DashboardNavigationTotals(
            active_connections=self._panel_total(
                dashboard_data.active_connections
            ),
            active_alarms=self._panel_total(
                dashboard_data.active_alarms
            ),
            recent_events=self._panel_total(
                dashboard_data.recent_events
            ),
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
            dashboard_data,
            navigation_state=self._navigation_state,
        )

    def run(
        self,
        *,
        refresh_interval_seconds: float = 1.0,
        max_iterations: int | None = None,
    ) -> None:
        """Ejecuta continuamente el dashboard utilizando Rich Live."""

        iteration = 0

        keyboard_input = getattr(
            self,
            "_keyboard_input",
            None,
        )
        key_parser = getattr(
            self,
            "_key_parser",
            None,
        )

        with ExitStack() as stack:
            live = stack.enter_context(
                Live(
                    screen=True,
                    auto_refresh=False,
                )
            )

            if keyboard_input is not None:
                keyboard_input = stack.enter_context(
                    keyboard_input
                )

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

                should_quit = DashboardApplication._wait_for_navigation_input(
                    self,
                    refresh_interval_seconds=(
                        refresh_interval_seconds
                    ),
                    keyboard_input=keyboard_input,
                    key_parser=key_parser,
                )

                if should_quit:
                    break

    def _wait_for_navigation_input(
        self,
        *,
        refresh_interval_seconds: float,
        keyboard_input: PosixKeyboardInput | None,
        key_parser: DashboardKeyParser | None,
    ) -> bool:
        """Espera el próximo refresh procesando navegación sin recapturar."""

        if (
            keyboard_input is None
            or key_parser is None
            or not keyboard_input.active
        ):
            sleep(refresh_interval_seconds)
            return False

        deadline = monotonic() + refresh_interval_seconds

        while True:
            remaining = deadline - monotonic()

            if remaining <= 0:
                return False

            sequence = keyboard_input.read_available(
                timeout_seconds=remaining,
            )

            if sequence is None:
                return False

            action = key_parser.parse(sequence)

            if action is None:
                continue

            if action is DashboardNavigationAction.QUIT:
                return True

            self.apply_navigation_action(action)

    @staticmethod
    def _panel_total(panel: object | None) -> int:
        """Obtiene un total navegable válido informado por un panel."""

        if panel is None:
            return 0

        total_items = getattr(
            panel,
            "total_items",
            None,
        )

        if (
            isinstance(total_items, bool)
            or not isinstance(total_items, int)
        ):
            return 0

        if total_items < 0:
            return 0

        return total_items

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

    def _validate_noc_dependencies(self) -> None:
        """Evita configurar parcialmente el runtime NOC."""

        dependencies = (
            self._telemetry_refresh_service,
            self._session_transition_event_service,
            self._event_service,
            self._alarm_service,
            self._history_query_service,
            self._node_id,
            self._instance_id,
        )

        configured_count = sum(
            dependency is not None
            for dependency in dependencies
        )

        if configured_count not in (
            0,
            len(dependencies),
        ):
            raise ValueError(
                "telemetry_refresh_service, "
                "session_transition_event_service, event_service, "
                "alarm_service, history_query_service, node_id e "
                "instance_id deben "
                "configurarse juntos."
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
