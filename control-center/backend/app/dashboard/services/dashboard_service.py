"""Servicio de aplicación para construir datos del dashboard."""

from app.dashboard.models import (
    DashboardData,
    PathRowData,
    ServerPanelData,
    StreamingPanelData,
)
from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    StreamingHealth,
    StreamingMeasurement,
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
        health: StreamingHealth | None = None,
    ) -> DashboardData:
        """Agrupa todas las secciones del dashboard."""

        return DashboardData(
            server=server,
            streaming=streaming,
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