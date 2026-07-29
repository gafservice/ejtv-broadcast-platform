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

    UTILIZATION_DEGRADED_PERCENT = 70.0
    UTILIZATION_CRITICAL_PERCENT = 90.0

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

        status = self._classify_connection(
            rtt_ms=rtt_ms,
            link_utilization_percent=(
                link_utilization_percent
            ),
        )

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

    def _classify_connection(
        self,
        *,
        rtt_ms: float | None,
        link_utilization_percent: float | None,
    ) -> HealthStatus:
        """Clasifica una conexión mediante RTT y utilización."""

        statuses: list[HealthStatus] = []

        if rtt_ms is not None:
            if rtt_ms >= self.RTT_CRITICAL_MS:
                statuses.append(HealthStatus.CRITICAL)
            elif rtt_ms >= self.RTT_DEGRADED_MS:
                statuses.append(HealthStatus.DEGRADED)
            else:
                statuses.append(HealthStatus.HEALTHY)

        if link_utilization_percent is not None:
            if (
                link_utilization_percent
                >= self.UTILIZATION_CRITICAL_PERCENT
            ):
                statuses.append(HealthStatus.CRITICAL)
            elif (
                link_utilization_percent
                >= self.UTILIZATION_DEGRADED_PERCENT
            ):
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
