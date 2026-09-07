"""Temporal stabilization of aggregated streaming health.

ENG-013B — Stream Health Block 2

This service applies connection-level temporal stabilization and rebuilds
effective path and global health from the stabilized connection states.

Current technical evidence remains associated with the current capture.
It does not create events or alarms.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from app.domain.streaming.health import (
    HealthStatus,
    SRTPathHealth,
    StreamingHealth,
)
from app.services.srt_connection_health_stabilizer import (
    SRTConnectionHealthStabilizer,
)


class StreamingHealthStabilizer:
    """Build effective streaming health from instantaneous observations."""

    def __init__(
        self,
        *,
        connection_stabilizer: SRTConnectionHealthStabilizer,
    ) -> None:
        self._connection_stabilizer = connection_stabilizer

    def stabilize(
        self,
        health: StreamingHealth,
    ) -> StreamingHealth:
        """Return temporally stabilized effective streaming health."""

        stabilized_paths = tuple(
            self._stabilize_path(
                path,
                observed_at=health.captured_at,
            )
            for path in health.paths
        )

        if not stabilized_paths:
            return health

        status = self._resolve_status(
            path.status
            for path in stabilized_paths
        )

        if (
            stabilized_paths == health.paths
            and status is health.status
        ):
            return health

        return replace(
            health,
            paths=stabilized_paths,
            status=status,
            message=self._global_message(status),
        )

    def _stabilize_path(
        self,
        path: SRTPathHealth,
        *,
        observed_at,
    ) -> SRTPathHealth:
        stabilized_connections = tuple(
            self._connection_stabilizer.stabilize(
                connection,
                observed_at=observed_at,
            )
            for connection in path.connections
        )

        status = self._resolve_status(
            connection.status
            for connection in stabilized_connections
        )

        if (
            stabilized_connections == path.connections
            and status is path.status
        ):
            return path

        return replace(
            path,
            connections=stabilized_connections,
            status=status,
            message=self._path_message(status),
        )

    @staticmethod
    def _resolve_status(
        statuses: Iterable[HealthStatus],
    ) -> HealthStatus:
        status_set = set(statuses)

        if HealthStatus.CRITICAL in status_set:
            return HealthStatus.CRITICAL

        if HealthStatus.DEGRADED in status_set:
            return HealthStatus.DEGRADED

        if HealthStatus.HEALTHY in status_set:
            return HealthStatus.HEALTHY

        return HealthStatus.UNKNOWN

    @staticmethod
    def _path_message(
        status: HealthStatus,
    ) -> str:
        messages = {
            HealthStatus.HEALTHY: "Path SRT estable.",
            HealthStatus.DEGRADED: "Path SRT degradado.",
            HealthStatus.CRITICAL: "Path SRT en estado crítico.",
            HealthStatus.UNKNOWN: "Salud del path SRT no determinada.",
        }

        return messages[status]

    @staticmethod
    def _global_message(
        status: HealthStatus,
    ) -> str:
        messages = {
            HealthStatus.HEALTHY: "Streaming SRT estable.",
            HealthStatus.DEGRADED: "El streaming SRT está degradado.",
            HealthStatus.CRITICAL: "El streaming SRT requiere atención.",
            HealthStatus.UNKNOWN: "Salud del streaming SRT no determinada.",
        }

        return messages[status]
