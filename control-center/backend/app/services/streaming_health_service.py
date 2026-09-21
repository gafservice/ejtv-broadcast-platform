"""Servicio que interpreta métricas SRT como salud operativa."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import isfinite
from statistics import mean
from typing import Iterable

from app.adapters.mediamtx.metrics_parser import (
    MediaMTXMetricsSnapshot,
    PrometheusSample,
)
from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionQuality,
    SessionRole,
    SessionSnapshot,
    evaluate_session_quality,
)
from app.domain.streaming.health import (
    HealthStatus,
    SRTConnectionHealth,
    SRTPathHealth,
    StreamingHealth,
)


class StreamingHealthService:
    """Transforma métricas técnicas en estados de salud del streaming."""

    RTT_DEGRADED_MS = 100.0
    RTT_CRITICAL_MS = 250.0

    _SUPPORTED_METRICS = frozenset(
        {
            "srt_conns_ms_rtt",
            "srt_conns_mbps_send_rate",
            "srt_conns_mbps_link_capacity",
            "srt_conns_packets_retrans",
            "srt_conns_packets_send_loss",
        }
    )

    def build(
        self,
        *,
        snapshot: MediaMTXMetricsSnapshot,
        captured_at: datetime,
        session_snapshot: SessionSnapshot | None = None,
        previous_session_snapshot: SessionSnapshot | None = None,
    ) -> StreamingHealth:
        """Construye el estado de salud a partir de un snapshot."""

        grouped_samples = self._group_connection_samples(
            snapshot.samples
        )

        if not grouped_samples:
            return StreamingHealth.empty(
                captured_at=captured_at
            )

        connections = tuple(
            self._build_connection(
                connection_id=connection_id,
                path_name=path_name,
                state=state,
                metrics=metrics,
                session_quality=self._resolve_effective_srt_session_quality(
                    previous_session_snapshot=previous_session_snapshot,
                    session_snapshot=session_snapshot,
                    connection_id=connection_id,
                ),
                temporal_session_evidence=(
                    previous_session_snapshot is not None
                ),
                session=(
                    self._find_srt_session(
                        session_snapshot=session_snapshot,
                        connection_id=connection_id,
                    )
                    if session_snapshot is not None
                    else None
                ),
            )
            for (
                connection_id,
                path_name,
                state,
            ), metrics in sorted(grouped_samples.items())
        )

        connections_by_path: dict[
            str,
            list[SRTConnectionHealth],
        ] = defaultdict(list)

        for connection in connections:
            connections_by_path[
                connection.path_name
            ].append(connection)

        paths = tuple(
            self._build_path(
                path_name=path_name,
                connections=tuple(path_connections),
            )
            for path_name, path_connections
            in sorted(connections_by_path.items())
        )

        status = self._resolve_status(
            path.status
            for path in paths
        )

        return StreamingHealth(
            captured_at=captured_at,
            paths=paths,
            status=status,
            message=self._build_global_message(status),
        )

    def _group_connection_samples(
        self,
        samples: tuple[PrometheusSample, ...],
    ) -> dict[
        tuple[str, str, str],
        dict[str, float],
    ]:
        """Agrupa métricas por conexión, path y estado."""

        grouped: dict[
            tuple[str, str, str],
            dict[str, float],
        ] = {}

        for sample in samples:
            if sample.name not in self._SUPPORTED_METRICS:
                continue

            connection_id = sample.labels.get("id", "").strip()
            path_name = sample.labels.get("path", "").strip()
            state = (
                sample.labels.get("state", "unknown").strip()
                or "unknown"
            )

            if not connection_id or not path_name:
                continue

            key = (
                connection_id,
                path_name,
                state,
            )

            grouped.setdefault(key, {})[
                sample.name
            ] = sample.value

        return grouped

    def _build_connection(
        self,
        *,
        connection_id: str,
        path_name: str,
        state: str,
        metrics: dict[str, float],
        session_quality: SessionQuality | None = None,
        temporal_session_evidence: bool = False,
        session: ActiveSession | None = None,
    ) -> SRTConnectionHealth:
        """Construye la salud de una conexión individual."""

        rtt_ms = self._read_non_negative_float(
            metrics.get("srt_conns_ms_rtt")
        )
        send_rate_mbps = self._read_non_negative_float(
            metrics.get("srt_conns_mbps_send_rate")
        )
        link_capacity_mbps = self._read_non_negative_float(
            metrics.get("srt_conns_mbps_link_capacity")
        )

        packets_retransmitted = self._read_counter(
            metrics.get("srt_conns_packets_retrans")
        )
        packets_lost = self._read_counter(
            metrics.get("srt_conns_packets_send_loss")
        )

        link_utilization_percent = self._calculate_utilization(
            send_rate_mbps=send_rate_mbps,
            link_capacity_mbps=link_capacity_mbps,
        )

        if session_quality is not None:
            status = self._health_status_from_session_quality(
                session_quality
            )
        elif temporal_session_evidence:
            status = HealthStatus.UNKNOWN
        else:
            status = self._classify_connection(rtt_ms=rtt_ms)

        return SRTConnectionHealth(
            connection_id=connection_id,
            path_name=path_name,
            state=state,
            rtt_ms=rtt_ms,
            packets_retransmitted=packets_retransmitted,
            packets_lost=packets_lost,
            status=status,
            message=self._build_connection_message(status),
            send_rate_mbps=send_rate_mbps,
            link_capacity_mbps=link_capacity_mbps,
            link_utilization_percent=(
                link_utilization_percent
            ),
            remote_address=(
                f"{session.remote_ip}:{session.remote_port}"
                if session is not None
                and session.remote_ip is not None
                and session.remote_port is not None
                else None
            ),
            role=(
                session.role.value
                if session is not None
                else None
            ),

        )

    def _build_path(
        self,
        *,
        path_name: str,
        connections: tuple[SRTConnectionHealth, ...],
    ) -> SRTPathHealth:
        """Construye el resumen de salud de un path."""

        rtt_values = tuple(
            connection.rtt_ms
            for connection in connections
            if connection.rtt_ms is not None
        )

        utilization_values = tuple(
            connection.link_utilization_percent
            for connection in connections
            if connection.link_utilization_percent is not None
        )

        retransmitted_values = tuple(
            connection.packets_retransmitted
            for connection in connections
            if connection.packets_retransmitted is not None
        )

        lost_values = tuple(
            connection.packets_lost
            for connection in connections
            if connection.packets_lost is not None
        )

        status = self._resolve_status(
            connection.status
            for connection in connections
        )

        return SRTPathHealth(
            name=path_name,
            connections=connections,
            average_rtt_ms=(
                mean(rtt_values)
                if rtt_values
                else None
            ),
            maximum_rtt_ms=(
                max(rtt_values)
                if rtt_values
                else None
            ),
            average_link_utilization_percent=(
                mean(utilization_values)
                if utilization_values
                else None
            ),
            total_packets_retransmitted=(
                sum(retransmitted_values)
                if retransmitted_values
                else None
            ),
            total_packets_lost=(
                sum(lost_values)
                if lost_values
                else None
            ),
            status=status,
            message=self._build_path_message(status),
        )

    @classmethod
    def _resolve_effective_srt_session_quality(
        cls,
        *,
        previous_session_snapshot: SessionSnapshot | None,
        session_snapshot: SessionSnapshot | None,
        connection_id: str,
    ) -> SessionQuality | None:
        """Selecciona calidad temporal o legado según evidencia disponible."""

        if previous_session_snapshot is not None:
            return cls._resolve_srt_session_quality(
                previous_session_snapshot=previous_session_snapshot,
                session_snapshot=session_snapshot,
                connection_id=connection_id,
            )

        if session_snapshot is None:
            return None

        session = cls._find_srt_session(
            session_snapshot=session_snapshot,
            connection_id=connection_id,
        )

        if session is None:
            return None

        return session.quality

    @classmethod
    def _resolve_srt_session_quality(
        cls,
        *,
        previous_session_snapshot: SessionSnapshot | None,
        session_snapshot: SessionSnapshot | None,
        connection_id: str,
    ) -> SessionQuality | None:
        """Evalúa calidad SRT usando deltas entre capturas compatibles."""

        if (
            previous_session_snapshot is None
            or session_snapshot is None
        ):
            return None

        interval_seconds = (
            session_snapshot.captured_at
            - previous_session_snapshot.captured_at
        ).total_seconds()

        if interval_seconds <= 0:
            return None

        current = cls._find_srt_session(
            session_snapshot=session_snapshot,
            connection_id=connection_id,
        )
        previous = cls._find_srt_session(
            session_snapshot=previous_session_snapshot,
            connection_id=connection_id,
        )

        if current is None or previous is None:
            return None

        if (
            current.path != previous.path
            or current.role is not previous.role
            or current.connected_since != previous.connected_since
        ):
            return None

        if current.role is not SessionRole.READER:
            return None

        if (
            current.packets_sent is None
            or previous.packets_sent is None
            or current.packets_lost is None
            or previous.packets_lost is None
        ):
            return None

        delta_sent = current.packets_sent - previous.packets_sent
        delta_lost = current.packets_lost - previous.packets_lost

        if delta_sent <= 0 or delta_lost < 0:
            return None

        delta_retransmitted: int | None = None

        if (
            current.packets_retransmitted is not None
            and previous.packets_retransmitted is not None
        ):
            candidate_delta = (
                current.packets_retransmitted
                - previous.packets_retransmitted
            )

            if candidate_delta < 0:
                return None

            delta_retransmitted = candidate_delta

        packet_loss_rate = delta_lost * 100.0 / delta_sent

        retransmission_rate = (
            delta_retransmitted * 100.0 / delta_sent
            if delta_retransmitted is not None
            else None
        )

        return evaluate_session_quality(
            rtt_ms=current.rtt_ms,
            packet_loss_rate=packet_loss_rate,
            retransmission_rate=retransmission_rate,
        )

    @staticmethod
    def _find_srt_session(
        *,
        session_snapshot: SessionSnapshot,
        connection_id: str,
    ) -> ActiveSession | None:
        """Busca una sesión SRT concreta dentro del snapshot."""

        for session in session_snapshot.sessions:
            if (
                session.protocol is SessionProtocol.SRT
                and session.session_id == connection_id
            ):
                return session

        return None

    @staticmethod
    def _health_status_from_session_quality(
        quality: SessionQuality,
    ) -> HealthStatus:
        if quality in (
            SessionQuality.EXCELLENT,
            SessionQuality.GOOD,
        ):
            return HealthStatus.HEALTHY

        if quality in (
            SessionQuality.FAIR,
            SessionQuality.POOR,
        ):
            return HealthStatus.DEGRADED

        if quality is SessionQuality.CRITICAL:
            return HealthStatus.CRITICAL

        return HealthStatus.UNKNOWN

    def _classify_connection(
        self,
        *,
        rtt_ms: float | None,
    ) -> HealthStatus:
        """Clasifica una conexión usando indicadores con semántica fiable."""

        statuses: list[HealthStatus] = []

        if rtt_ms is not None:
            if rtt_ms >= self.RTT_CRITICAL_MS:
                statuses.append(HealthStatus.CRITICAL)
            elif rtt_ms >= self.RTT_DEGRADED_MS:
                statuses.append(HealthStatus.DEGRADED)
            else:
                statuses.append(HealthStatus.HEALTHY)

        return self._resolve_status(statuses)

    @staticmethod
    def _resolve_status(
        statuses: Iterable[HealthStatus],
    ) -> HealthStatus:
        """Retorna el estado más severo de una colección."""

        status_set = set(statuses)

        if HealthStatus.CRITICAL in status_set:
            return HealthStatus.CRITICAL

        if HealthStatus.DEGRADED in status_set:
            return HealthStatus.DEGRADED

        if HealthStatus.HEALTHY in status_set:
            return HealthStatus.HEALTHY

        return HealthStatus.UNKNOWN

    @staticmethod
    def _calculate_utilization(
        *,
        send_rate_mbps: float | None,
        link_capacity_mbps: float | None,
    ) -> float | None:
        """Calcula el porcentaje utilizado del enlace."""

        if (
            send_rate_mbps is None
            or link_capacity_mbps is None
            or link_capacity_mbps <= 0
        ):
            return None

        return (
            send_rate_mbps
            / link_capacity_mbps
            * 100
        )

    @staticmethod
    def _read_non_negative_float(
        value: float | None,
    ) -> float | None:
        """Normaliza una métrica flotante."""

        if value is None:
            return None

        if not isfinite(value) or value < 0:
            return None

        return value

    @staticmethod
    def _read_counter(
        value: float | None,
    ) -> int | None:
        """Normaliza un contador Prometheus."""

        if value is None:
            return None

        if (
            not isfinite(value)
            or value < 0
            or not value.is_integer()
        ):
            return None

        return int(value)

    @staticmethod
    def _build_connection_message(
        status: HealthStatus,
    ) -> str:
        messages = {
            HealthStatus.HEALTHY: "Conexión SRT estable.",
            HealthStatus.DEGRADED: "Conexión SRT degradada.",
            HealthStatus.CRITICAL: "Conexión SRT en estado crítico.",
            HealthStatus.UNKNOWN: "Salud de conexión no determinada.",
        }

        return messages[status]

    @staticmethod
    def _build_path_message(
        status: HealthStatus,
    ) -> str:
        messages = {
            HealthStatus.HEALTHY: "Todas las conexiones están estables.",
            HealthStatus.DEGRADED: "El path contiene conexiones degradadas.",
            HealthStatus.CRITICAL: "El path contiene conexiones críticas.",
            HealthStatus.UNKNOWN: "No fue posible evaluar el path.",
        }

        return messages[status]

    @staticmethod
    def _build_global_message(
        status: HealthStatus,
    ) -> str:
        messages = {
            HealthStatus.HEALTHY: "El streaming SRT está estable.",
            HealthStatus.DEGRADED: "El streaming SRT presenta degradación.",
            HealthStatus.CRITICAL: "El streaming SRT requiere atención.",
            HealthStatus.UNKNOWN: "No fue posible evaluar el streaming SRT.",
        }

        return messages[status]
