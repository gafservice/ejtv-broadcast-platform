"""Servicio de aplicación para construir datos del dashboard."""

from app.dashboard.models import (
    ActiveConnectionRow,
    ActiveConnectionsPanelData,
    CpuPanelData,
    DashboardData,
    DiskPanelData,
    MemoryPanelData,
    NetworkInterfaceRowData,
    NetworkInterfacesPanelData,
    NetworkPanelData,
    PathRowData,
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
    StreamingHealth,
    StreamingMeasurement,
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

    def build_session_panel(
        self,
        *,
        measurement: SessionMeasurement,
    ) -> SessionPanelData:
        """Construye los datos del panel ACTIVE CLIENTS."""

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
                measurement.total_outbound_bitrate_mbps
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
    ) -> ActiveConnectionsPanelData:
        """Construye los datos del panel CONNECTED CLIENTS."""

        connections = tuple(
            ActiveConnectionRow(
                remote_address=session.remote_address,
                country=session.location_label,
                country_code=session.country_code,
                asn=session.asn,
                provider=session.provider or "Unknown",
                protocol=session.protocol.value,
                path=session.path or "(sin path)",
                role=session.role.value,
                bitrate_bps=(
                    session.effective_bitrate_mbps * 1_000_000
                    if session.effective_bitrate_mbps is not None
                    else None
                ),
                uptime_seconds=session.duration_seconds(
                    now=measurement.captured_at,
                ),
                username=session.username,
            )
            for session in measurement.sessions
        )

        return ActiveConnectionsPanelData(
            captured_at=measurement.captured_at,
            connections=connections,
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
        system_resources: SystemResources | None = None,
        previous_system_resources: SystemResources | None = None,
        health: StreamingHealth | None = None,
        network_interfaces: NetworkInterfacesPanelData | None = None,
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
            )
            if session_measurement is not None
            else None
        )
        active_connections = (
            self.build_active_connections_panel(
                measurement=session_measurement,
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
