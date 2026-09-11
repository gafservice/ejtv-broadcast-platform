"""Servicio de aplicación para construir datos del dashboard."""

from app.dashboard.models.panel_viewport import PanelViewport
from app.dashboard.models import (
    ActiveAlarmRowData,
    ActiveAlarmsPanelData,
    ActiveConnectionRow,
    ActiveConnectionsPanelData,
    CpuPanelData,
    DashboardData,
    DiskPanelData,
    MemoryPanelData,
    NetworkInterfaceRowData,
    NetworkInterfacesPanelData,
    NetworkPanelData,
    NodeHealthInterfaceRowData,
    NodeHealthPanelData,
    PathRowData,
    PlatformHealthPanelData,
    RecentEventRowData,
    RecentEventsPanelData,
    ServerPanelData,
    SessionPanelData,
    StreamingPanelData,
    SystemPanelData,
    UptimePanelData,
)
from app.domain.sessions.measurement import SessionMeasurement
from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    RTMPConnectionHealth,
    StreamingHealth,
    StreamingMeasurement,
)
from app.domain.streaming.aggregation import PlatformHealth
from app.noc.domain.node_event import EventRecord
from app.noc.domain.node_alarm import AlarmRecord
from app.noc.domain.node_health_diagnostic import (
    NodeHealthDiagnostic,
)

from app.domain.system import (
    NetworkInterfaceTelemetry,
    NetworkRateCalculator,
    SystemResources,
)


_SOURCE_LABELS = {
    "mpegtsSource": "MPEG-TS",
    "udpSource": "UDP",
    "rtmpSource": "RTMP",
    "rtspSource": "RTSP",
    "srtSource": "SRT",
    "hlsSource": "HLS",
    "webRTCSource": "WebRTC",
}


class DashboardService:
    """Coordina la construcción de la información del dashboard."""

    def __init__(
        self,
        network_rate_calculator: NetworkRateCalculator | None = None,
    ) -> None:
        """Configura los calculadores usados por el servicio."""

        self._network_rate_calculator = (
            network_rate_calculator
            or NetworkRateCalculator()
        )

    def build_server_panel(
        self,
        *,
        hostname: str,
        mediamtx_online: bool,
        api_online: bool,
        snapshot: MediaMTXSnapshot,
        quality: MeasurementQuality,
    ) -> ServerPanelData:
        """Construye los datos del panel SERVER."""

        return ServerPanelData(
            hostname=hostname,
            mediamtx_online=mediamtx_online,
            api_online=api_online,
            snapshot_at=snapshot.captured_at,
            quality=quality.value,
        )

    def build_streaming_panel(
        self,
        *,
        active_paths: int,
        readers: int,
        inbound_bitrate_bps: float | None,
        outbound_bitrate_bps: float | None,
        quality: MeasurementQuality,
    ) -> StreamingPanelData:
        """Construye los datos del panel STREAMING."""

        return StreamingPanelData(
            active_paths=active_paths,
            readers=readers,
            inbound_bitrate_bps=inbound_bitrate_bps,
            outbound_bitrate_bps=outbound_bitrate_bps,
            quality=quality.value,
        )


    def build_platform_health_panel(
        self,
        *,
        platform_health: PlatformHealth,
    ) -> PlatformHealthPanelData:
        """Proyecta PLATFORM HEALTH al modelo de presentación."""

        population = platform_health.population

        return PlatformHealthPanelData(
            status=platform_health.status.value,
            worst_status=platform_health.worst_observed_status.value,
            healthy_count=population.healthy_count,
            degraded_count=population.degraded_count,
            critical_count=population.critical_count,
            unknown_count=population.unknown_count,
            evidence_coverage=population.evidence_coverage,
            affected_fraction=population.affected_fraction,
            service_count=len(platform_health.services),
            captured_at=platform_health.captured_at,
        )

    def build_session_panel(
        self,
        *,
        measurement: SessionMeasurement,
        rtmp_connections: tuple[RTMPConnectionHealth, ...] = (),
    ) -> SessionPanelData:
        """Construye los datos del panel ACTIVE CLIENTS."""

        rtmp_health_by_key = {}
        ambiguous_rtmp_health_keys = set()

        for connection in rtmp_connections:
            key = (
                connection.connection_id,
                connection.path_name,
            )

            if key in rtmp_health_by_key:
                ambiguous_rtmp_health_keys.add(key)
                continue

            rtmp_health_by_key[key] = connection

        outbound_bitrate_mbps = measurement.total_outbound_bitrate_mbps

        for session in measurement.sessions:
            key = (
                session.session_id,
                session.path,
            )

            if (
                session.protocol.value != "RTMP"
                or session.role.value != "READER"
                or key not in rtmp_health_by_key
                or key in ambiguous_rtmp_health_keys
            ):
                continue

            specialized_bitrate_mbps = (
                rtmp_health_by_key[key].effective_bitrate_mbps
            )

            if specialized_bitrate_mbps is None:
                continue

            native_bitrate_mbps = (
                session.bitrate_send_mbps or 0.0
            )

            outbound_bitrate_mbps = (
                outbound_bitrate_mbps
                - native_bitrate_mbps
                + specialized_bitrate_mbps
            )

        return SessionPanelData(
            total_sessions=measurement.total_sessions,
            readers=measurement.reader_count,
            publishers=measurement.publisher_count,
            degraded_sessions=measurement.degraded_session_count,
            critical_sessions=measurement.critical_session_count,
            inbound_bitrate_bps=(
                measurement.total_inbound_bitrate_mbps
                * 1_000_000
            ),
            outbound_bitrate_bps=(
                outbound_bitrate_mbps
                * 1_000_000
            ),
            quality=measurement.worst_quality.value,
            protocol_counts=tuple(
                (
                    protocol.value,
                    count,
                )
                for protocol, count in measurement.protocol_counts
            ),
        )

    def build_active_connections_panel(
        self,
        *,
        measurement: SessionMeasurement,
        health: StreamingHealth | None = None,
        rtmp_connections: tuple[RTMPConnectionHealth, ...] = (),
        viewport: PanelViewport | None = None,
    ) -> ActiveConnectionsPanelData:
        """Construye los datos del panel CONNECTED CLIENTS."""

        srt_health_by_key = {}
        ambiguous_srt_health_keys = set()

        if health is not None:
            for path_health in health.paths:
                for connection in path_health.connections:
                    key = (
                        connection.connection_id,
                        connection.path_name,
                    )

                    if key in srt_health_by_key:
                        ambiguous_srt_health_keys.add(key)
                        continue

                    srt_health_by_key[key] = connection

        rtmp_health_by_key = {}
        ambiguous_rtmp_health_keys = set()

        for connection in rtmp_connections:
            key = (
                connection.connection_id,
                connection.path_name,
            )

            if key in rtmp_health_by_key:
                ambiguous_rtmp_health_keys.add(key)
                continue

            rtmp_health_by_key[key] = connection

        connections = tuple(
            ActiveConnectionRow(
                session_id=session.session_id,
                remote_address=session.remote_address,
                country=session.location_label,
                country_code=session.country_code,
                asn=session.asn,
                provider=session.provider or "Unknown",
                protocol=session.protocol.value,
                path=session.path or "(sin path)",
                role=session.role.value,
                bitrate_bps=(
                    rtmp_health_by_key[
                        (session.session_id, session.path)
                    ].effective_bitrate_mbps
                    * 1_000_000
                    if (
                        session.protocol.value == "RTMP"
                        and (
                            session.session_id,
                            session.path,
                        ) in rtmp_health_by_key
                        and (
                            session.session_id,
                            session.path,
                        ) not in ambiguous_rtmp_health_keys
                        and rtmp_health_by_key[
                            (session.session_id, session.path)
                        ].effective_bitrate_mbps
                        is not None
                    )
                    else (
                        session.effective_bitrate_mbps * 1_000_000
                        if session.effective_bitrate_mbps is not None
                        else None
                    )
                ),
                uptime_seconds=session.duration_seconds(
                    now=measurement.captured_at,
                ),
                username=session.username,
                health=(
                    srt_health_by_key[
                        (session.session_id, session.path)
                    ].status.value
                    if (
                        session.protocol.value == "SRT"
                        and (
                            session.session_id,
                            session.path,
                        ) in srt_health_by_key
                        and (
                            session.session_id,
                            session.path,
                        ) not in ambiguous_srt_health_keys
                    )
                    else (
                        rtmp_health_by_key[
                            (session.session_id, session.path)
                        ].status.value
                        if (
                            session.protocol.value == "RTMP"
                            and (
                                session.session_id,
                                session.path,
                            ) in rtmp_health_by_key
                            and (
                                session.session_id,
                                session.path,
                            ) not in ambiguous_rtmp_health_keys
                        )
                        else None
                    )
                ),
            )
            for session in measurement.sessions
        )

        selected_connections = self._apply_viewport(
            connections,
            viewport,
        )

        return ActiveConnectionsPanelData(
            captured_at=measurement.captured_at,
            connections=selected_connections,
            total_items=len(connections),
        )

    def build_active_alarms_panel(
        self,
        *,
        alarms: tuple[AlarmRecord, ...],
        viewport: PanelViewport | None = None,
    ) -> ActiveAlarmsPanelData:
        """Prepara alarmas operacionales activas para presentación."""

        if not isinstance(alarms, tuple):
            raise TypeError(
                "alarms must be a tuple"
            )

        for alarm in alarms:
            if not isinstance(
                alarm,
                AlarmRecord,
            ):
                raise TypeError(
                    "alarms must contain "
                    "AlarmRecord objects"
                )

        attention = tuple(
            alarm
            for alarm in alarms
            if alarm.requires_attention
        )

        ordered = sorted(
            attention,
            key=lambda alarm: alarm.timestamp,
            reverse=True,
        )

        selected = self._apply_viewport(
            tuple(ordered),
            viewport,
        )

        rows = tuple(
            ActiveAlarmRowData(
                alarm_id=alarm.alarm_id,
                alarm_type=alarm.alarm_type,
                severity=alarm.severity.value,
                state=alarm.state.value,
                message=alarm.title,
                opened_at=alarm.timestamp,
                remote_address=self._attribute_value(
                    alarm.attributes,
                    "remote_address",
                    fallback=self._attribute_value(
                        alarm.attributes,
                        "remote_ip",
                    ),
                ),
                path=self._attribute_value(
                    alarm.attributes,
                    "path",
                ),
                protocol=self._attribute_value(
                    alarm.attributes,
                    "protocol",
                ),
                role=self._attribute_value(
                    alarm.attributes,
                    "role",
                ),
            )
            for alarm in selected
        )

        return ActiveAlarmsPanelData(
            alarms=rows,
            total_items=len(attention),
        )

    def build_recent_events_panel(
        self,
        *,
        events: tuple[EventRecord, ...],
        viewport: PanelViewport | None = None,
    ) -> RecentEventsPanelData:
        """Prepara eventos operacionales recientes para presentación."""

        if not isinstance(events, tuple):
            raise TypeError(
                "events must be a tuple"
            )

        for event in events:
            if not isinstance(
                event,
                EventRecord,
            ):
                raise TypeError(
                    "events must contain "
                    "EventRecord objects"
                )

        ordered = sorted(
            events,
            key=lambda event: event.timestamp,
            reverse=True,
        )

        selected = self._apply_viewport(
            tuple(ordered),
            viewport,
        )

        rows = tuple(
            RecentEventRowData(
                event_id=event.event_id,
                event_type=event.event_type,
                severity=event.severity.value,
                title=event.title,
                occurred_at=event.timestamp,
                remote_address=self._attribute_value(
                    event.attributes,
                    "remote_address",
                    fallback=self._attribute_value(
                        event.attributes,
                        "remote_ip",
                    ),
                ),
                path=self._attribute_value(
                    event.attributes,
                    "path",
                ),
                protocol=self._attribute_value(
                    event.attributes,
                    "protocol",
                ),
                role=self._attribute_value(
                    event.attributes,
                    "role",
                ),
            )
            for event in selected
        )

        return RecentEventsPanelData(
            events=rows,
            total_items=len(ordered),
        )

    @staticmethod
    def _apply_viewport(
        items: tuple,
        viewport: PanelViewport | None,
    ) -> tuple:
        """Aplica una ventana visible sin alterar la colección fuente."""

        if viewport is None:
            return items

        if not isinstance(viewport, PanelViewport):
            raise TypeError(
                "viewport must be a PanelViewport"
            )

        start, end = viewport.bounds(
            len(items)
        )

        return items[start:end]

    @staticmethod
    def _attribute_value(
        attributes,
        key: str,
        *,
        fallback: str = "-",
    ) -> str:
        """Return normalized dashboard text from record attributes."""

        if attributes is None:
            return fallback

        value = attributes.get(key)

        if value is None:
            return fallback

        normalized = str(value).strip()

        return normalized or fallback

    def build_node_health_panel(
        self,
        *,
        diagnostic: NodeHealthDiagnostic,
    ) -> NodeHealthPanelData:
        """Prepara el diagnóstico integral del Node para presentación."""

        if not isinstance(
            diagnostic,
            NodeHealthDiagnostic,
        ):
            raise TypeError(
                "diagnostic must be a NodeHealthDiagnostic"
            )

        interfaces = tuple(
            NodeHealthInterfaceRowData(
                interface=item.interface,
                state=item.state.value,
                reason=item.reason,
                error_rate=item.error_rate,
                drop_rate=item.drop_rate,
            )
            for item in diagnostic.network_interfaces
        )

        return NodeHealthPanelData(
            state=diagnostic.health.state.value,
            system_state=diagnostic.system_health.state.value,
            network_state=diagnostic.network_health.state.value,
            interfaces=interfaces,
            captured_at=diagnostic.captured_at,
        )

    def build_network_interfaces_panel(
        self,
        *,
        telemetry: tuple[
            NetworkInterfaceTelemetry,
            ...,
        ],
    ) -> NetworkInterfacesPanelData:
        """Prepara la telemetría Multi-Interface para presentación."""

        if not isinstance(telemetry, tuple):
            raise TypeError(
                "telemetry must be a tuple"
            )

        rows: list[NetworkInterfaceRowData] = []

        captured_at = None

        for item in telemetry:
            if not isinstance(
                item,
                NetworkInterfaceTelemetry,
            ):
                raise TypeError(
                    "telemetry must contain "
                    "NetworkInterfaceTelemetry objects"
                )

            rates = item.rates

            if captured_at is None and rates is not None:
                captured_at = rates.captured_at

            rows.append(
                NetworkInterfaceRowData(
                    interface=item.info.interface,
                    interface_type=(
                        item.info.interface_type.value
                    ),
                    is_up=item.info.is_up,
                    carrier=item.info.carrier,
                    link_speed_mbps=(
                        item.info.link_speed_mbps
                    ),
                    mtu=item.info.mtu,
                    mac_address=item.info.mac_address,
                    ipv4_addresses=(
                        item.info.ipv4_addresses
                    ),
                    ipv6_addresses=(
                        item.info.ipv6_addresses
                    ),
                    rx_bps=(
                        rates.rx_bps
                        if rates is not None
                        else None
                    ),
                    tx_bps=(
                        rates.tx_bps
                        if rates is not None
                        else None
                    ),
                    errors_in=item.counters.errors_in,
                    errors_out=item.counters.errors_out,
                    dropped_in=item.counters.dropped_in,
                    dropped_out=item.counters.dropped_out,
                    errors_in_per_second=(
                        rates.errors_in_per_second
                        if rates is not None
                        else None
                    ),
                    errors_out_per_second=(
                        rates.errors_out_per_second
                        if rates is not None
                        else None
                    ),
                    dropped_in_per_second=(
                        rates.dropped_in_per_second
                        if rates is not None
                        else None
                    ),
                    dropped_out_per_second=(
                        rates.dropped_out_per_second
                        if rates is not None
                        else None
                    ),
                )
            )

        if captured_at is None:
            raise ValueError(
                "No se pudo determinar captured_at "
                "de la telemetría."
            )

        return NetworkInterfacesPanelData(
            interfaces=tuple(rows),
            captured_at=captured_at,
        )

    def build_system_panel(
        self,
        *,
        resources: SystemResources,
        previous_resources: SystemResources | None = None,
    ) -> SystemPanelData:
        """Construye los datos del panel SYSTEM."""

        network_rate = self._network_rate_calculator.compare(
            previous_resources,
            resources,
        )

        return SystemPanelData(
            cpu=CpuPanelData(
                usage_percent=resources.cpu.usage_percent,
                per_core_usage_percent=(
                    resources.cpu.per_core_usage_percent
                ),
                logical_cores=resources.cpu.logical_cores,
                physical_cores=resources.cpu.physical_cores,
                frequency_mhz=resources.cpu.frequency_mhz,
            ),
            memory=MemoryPanelData(
                usage_percent=resources.memory.usage_percent,
                used_bytes=resources.memory.used_bytes,
                total_bytes=resources.memory.total_bytes,
            ),
            disk=DiskPanelData(
                usage_percent=resources.disk.usage_percent,
                used_bytes=resources.disk.used_bytes,
                total_bytes=resources.disk.total_bytes,
            ),
            network=NetworkPanelData(
                interface=network_rate.interface,
                rx_bps=network_rate.rx_bps,
                tx_bps=network_rate.tx_bps,
                errors_in=network_rate.errors_in,
                errors_out=network_rate.errors_out,
                dropped_in=network_rate.dropped_in,
                dropped_out=network_rate.dropped_out,
                errors_in_per_second=(
                    network_rate.errors_in_per_second
                ),
                errors_out_per_second=(
                    network_rate.errors_out_per_second
                ),
                dropped_in_per_second=(
                    network_rate.dropped_in_per_second
                ),
                dropped_out_per_second=(
                    network_rate.dropped_out_per_second
                ),
            ),
            uptime=UptimePanelData(
                seconds=resources.uptime.uptime_seconds,
            ),
            captured_at=resources.captured_at,
        )

    def build_path_row(
        self,
        *,
        name: str,
        status: str,
        readers: int,
        inbound_bitrate_bps: float | None,
        outbound_bitrate_bps: float | None,
        quality: MeasurementQuality,
        source: str,
    ) -> PathRowData:
        """Construye una fila para la tabla de paths."""

        return PathRowData(
            name=name,
            status=status,
            readers=readers,
            inbound_bitrate_bps=inbound_bitrate_bps,
            outbound_bitrate_bps=outbound_bitrate_bps,
            quality=quality.value,
            source=source,
        )

    def build_dashboard(
        self,
        *,
        server: ServerPanelData,
        streaming: StreamingPanelData,
        sessions: SessionPanelData | None = None,
        active_connections: ActiveConnectionsPanelData | None = None,
        paths: tuple[PathRowData, ...],
        system: SystemPanelData | None = None,
        health: StreamingHealth | None = None,
        network_interfaces: NetworkInterfacesPanelData | None = None,
        node_health: NodeHealthPanelData | None = None,
        recent_events: RecentEventsPanelData | None = None,
        active_alarms: ActiveAlarmsPanelData | None = None,
        platform_health: PlatformHealthPanelData | None = None,
        active_connections_viewport: PanelViewport | None = None,
    ) -> DashboardData:
        """Agrupa todas las secciones del dashboard."""

        return DashboardData(
            server=server,
            streaming=streaming,
            sessions=sessions,
            active_connections=active_connections,
            system=system,
            paths=paths,
            health=health,
            network_interfaces=network_interfaces,
            node_health=node_health,
            recent_events=recent_events,
            active_alarms=active_alarms,
            platform_health=platform_health,
        )

    def build_dashboard_from_measurement(
        self,
        *,
        hostname: str,
        mediamtx_online: bool,
        api_online: bool,
        snapshot: MediaMTXSnapshot,
        measurement: StreamingMeasurement,
        session_measurement: SessionMeasurement | None = None,
        rtmp_connections: tuple[RTMPConnectionHealth, ...] = (),
        system_resources: SystemResources | None = None,
        previous_system_resources: SystemResources | None = None,
        health: StreamingHealth | None = None,
        network_interfaces: NetworkInterfacesPanelData | None = None,
        node_health: NodeHealthPanelData | None = None,
        recent_events: RecentEventsPanelData | None = None,
        active_alarms: ActiveAlarmsPanelData | None = None,
        platform_health: PlatformHealth | None = None,
        active_connections_viewport: PanelViewport | None = None,
    ) -> DashboardData:
        """Construye el dashboard completo desde snapshot y medición."""

        if snapshot.captured_at != measurement.captured_at:
            raise ValueError(
                "snapshot y measurement deben pertenecer al mismo instante"
            )

        if (
            health is not None
            and health.captured_at != snapshot.captured_at
        ):
            raise ValueError(
                "snapshot, measurement y health deben pertenecer "
                "al mismo instante"
            )

        path_names = [
            path_measurement.name
            for path_measurement in measurement.paths
        ]

        if len(path_names) != len(set(path_names)):
            raise ValueError(
                "measurement contiene nombres de paths duplicados"
            )

        server = self.build_server_panel(
            hostname=hostname,
            mediamtx_online=mediamtx_online,
            api_online=api_online,
            snapshot=snapshot,
            quality=measurement.quality,
        )

        streaming = self.build_streaming_panel(
            active_paths=snapshot.active_path_count,
            readers=measurement.total_reader_count,
            inbound_bitrate_bps=measurement.total_inbound_bitrate_bps,
            outbound_bitrate_bps=measurement.total_outbound_bitrate_bps,
            quality=measurement.quality,
        )

        sessions = (
            self.build_session_panel(
                measurement=session_measurement,
                rtmp_connections=rtmp_connections,
            )
            if session_measurement is not None
            else None
        )
        active_connections = (
            self.build_active_connections_panel(
                measurement=session_measurement,
                health=health,
                rtmp_connections=rtmp_connections,
                viewport=active_connections_viewport,
            )
            if session_measurement is not None
            else None
        )

        system = (
            self.build_system_panel(
                resources=system_resources,
                previous_resources=previous_system_resources,
            )
            if system_resources is not None
            else None
        )

        platform_health_panel = (
            self.build_platform_health_panel(
                platform_health=platform_health,
            )
            if platform_health is not None
            else None
        )

        paths = tuple(
            self.build_path_row(
                name=path_measurement.name,
                status=path_measurement.status.value,
                readers=path_measurement.reader_count,
                inbound_bitrate_bps=(
                    path_measurement.inbound_bitrate_bps
                ),
                outbound_bitrate_bps=(
                    path_measurement.outbound_bitrate_bps
                ),
                quality=path_measurement.quality,
                source=self._resolve_source(
                    snapshot=snapshot,
                    path_name=path_measurement.name,
                ),
            )
            for path_measurement in measurement.paths
        )

        return self.build_dashboard(
            server=server,
            streaming=streaming,
            sessions=sessions,
            active_connections=active_connections,
            system=system,
            paths=paths,
            health=health,
            network_interfaces=network_interfaces,
            node_health=node_health,
            recent_events=recent_events,
            active_alarms=active_alarms,
            platform_health=platform_health_panel,
        )

    @staticmethod
    def _resolve_source(
        *,
        snapshot: MediaMTXSnapshot,
        path_name: str,
    ) -> str:
        """Obtiene la etiqueta legible de la fuente o retorna NONE."""

        snapshot_path = snapshot.get_path(path_name)

        if snapshot_path is None or snapshot_path.source is None:
            return "NONE"

        source_type = snapshot_path.source.source_type

        source_labels = {
            "udpSource": "UDP",
            "mpegtsSource": "MPEG-TS",
            "srtSource": "SRT",
            "rtspSource": "RTSP",
            "rtmpSource": "RTMP",
            "hlsSource": "HLS",
            "webRTCSource": "WebRTC",
        }

        return source_labels.get(source_type, source_type)
