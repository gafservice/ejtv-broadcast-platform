"""Servicio de aplicación para construir datos del dashboard."""

from app.dashboard.models import (
    DashboardData,
    PathRowData,
    ServerPanelData,
    StreamingPanelData,
    SystemPanelData,
)
from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    StreamingHealth,
    StreamingMeasurement,
)
from app.domain.system import SystemResources


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

    def build_system_panel(
        self,
        *,
        resources: SystemResources,
    ) -> SystemPanelData:
        """Construye los datos del panel SYSTEM."""

        return SystemPanelData(
            cpu_usage_percent=resources.cpu.usage_percent,
            per_core_usage_percent=(
                resources.cpu.per_core_usage_percent
            ),
            logical_cores=resources.cpu.logical_cores,
            physical_cores=resources.cpu.physical_cores,
            frequency_mhz=resources.cpu.frequency_mhz,
            memory_usage_percent=resources.memory.usage_percent,
            memory_used_bytes=resources.memory.used_bytes,
            memory_total_bytes=resources.memory.total_bytes,
            disk_usage_percent=resources.disk.usage_percent,
            disk_used_bytes=resources.disk.used_bytes,
            disk_total_bytes=resources.disk.total_bytes,
            uptime_seconds=resources.uptime.uptime_seconds,
            network_interface=resources.network.interface,
            network_bytes_sent=resources.network.bytes_sent,
            network_bytes_received=resources.network.bytes_received,
            network_errors_in=resources.network.errors_in,
            network_errors_out=resources.network.errors_out,
            network_dropped_in=resources.network.dropped_in,
            network_dropped_out=resources.network.dropped_out,
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
        paths: tuple[PathRowData, ...],
        system: SystemPanelData | None = None,
        health: StreamingHealth | None = None,
    ) -> DashboardData:
        """Agrupa todas las secciones del dashboard."""

        return DashboardData(
            server=server,
            streaming=streaming,
            system=system,
            paths=paths,
            health=health,
        )

    def build_dashboard_from_measurement(
        self,
        *,
        hostname: str,
        mediamtx_online: bool,
        api_online: bool,
        snapshot: MediaMTXSnapshot,
        measurement: StreamingMeasurement,
        system_resources: SystemResources | None = None,
        health: StreamingHealth | None = None,
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

        system = (
            self.build_system_panel(resources=system_resources)
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
            system=system,
            paths=paths,
            health=health,
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

        return _SOURCE_LABELS.get(source_type, source_type)