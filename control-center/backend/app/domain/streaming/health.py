"""Modelos de dominio para evaluar la salud del streaming."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from math import isfinite


class HealthStatus(StrEnum):
    """Nivel operativo de salud de una conexión o path."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class SRTConnectionHealth:
    """Salud observada de una conexión SRT individual."""

    connection_id: str
    path_name: str
    state: str

    rtt_ms: float | None
    packets_retransmitted: int | None
    packets_lost: int | None

    status: HealthStatus
    message: str

    send_rate_mbps: float | None = None
    link_capacity_mbps: float | None = None
    link_utilization_percent: float | None = None

    def __post_init__(self) -> None:
        """Valida y normaliza la información de la conexión."""

        connection_id = self.connection_id.strip()
        path_name = self.path_name.strip()
        state = self.state.strip()
        message = self.message.strip()

        if not connection_id:
            raise ValueError(
                "connection_id debe contener texto válido."
            )

        if not path_name:
            raise ValueError(
                "path_name debe contener texto válido."
            )

        if not state:
            raise ValueError(
                "state debe contener texto válido."
            )

        if not message:
            raise ValueError(
                "message debe contener texto válido."
            )

        self._validate_optional_float("rtt_ms", self.rtt_ms)
        self._validate_optional_float(
            "send_rate_mbps",
            self.send_rate_mbps,
        )
        self._validate_optional_float(
            "link_capacity_mbps",
            self.link_capacity_mbps,
        )
        self._validate_optional_float(
            "link_utilization_percent",
            self.link_utilization_percent,
        )

        self._validate_optional_integer(
            "packets_retransmitted",
            self.packets_retransmitted,
        )
        self._validate_optional_integer(
            "packets_lost",
            self.packets_lost,
        )

        object.__setattr__(self, "connection_id", connection_id)
        object.__setattr__(self, "path_name", path_name)
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "message", message)

    @staticmethod
    def _validate_optional_float(
        field_name: str,
        value: float | None,
    ) -> None:
        if value is not None and (
            not isfinite(value)
            or value < 0
        ):
            raise ValueError(
                f"{field_name} debe ser finito y no negativo."
            )

    @staticmethod
    def _validate_optional_integer(
        field_name: str,
        value: int | None,
    ) -> None:
        if value is not None and value < 0:
            raise ValueError(
                f"{field_name} no puede ser negativo."
            )


@dataclass(frozen=True, slots=True)
class SRTPathHealth:
    """Resumen de salud de todas las conexiones SRT de un path."""

    name: str
    connections: tuple[SRTConnectionHealth, ...]

    average_rtt_ms: float | None
    total_packets_retransmitted: int | None
    total_packets_lost: int | None

    status: HealthStatus
    message: str

    maximum_rtt_ms: float | None = None
    average_link_utilization_percent: float | None = None

    def __post_init__(self) -> None:
        """Valida la coherencia interna del resumen del path."""

        name = self.name.strip()
        message = self.message.strip()

        if not name:
            raise ValueError(
                "El nombre del path debe contener texto válido."
            )

        if not message:
            raise ValueError(
                "El mensaje del path debe contener texto válido."
            )

        for field_name, value in (
            ("average_rtt_ms", self.average_rtt_ms),
            ("maximum_rtt_ms", self.maximum_rtt_ms),
            (
                "average_link_utilization_percent",
                self.average_link_utilization_percent,
            ),
        ):
            if value is not None and (
                not isfinite(value)
                or value < 0
            ):
                raise ValueError(
                    f"{field_name} debe ser finito y no negativo."
                )

        for field_name, value in (
            (
                "total_packets_retransmitted",
                self.total_packets_retransmitted,
            ),
            ("total_packets_lost", self.total_packets_lost),
        ):
            if value is not None and value < 0:
                raise ValueError(
                    f"{field_name} no puede ser negativo."
                )

        invalid_connections = tuple(
            connection.connection_id
            for connection in self.connections
            if connection.path_name != name
        )

        if invalid_connections:
            raise ValueError(
                "Todas las conexiones deben pertenecer al mismo path."
            )

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "message", message)

    @property
    def connection_count(self) -> int:
        """Cantidad de conexiones SRT asociadas al path."""

        return len(self.connections)


@dataclass(frozen=True, slots=True)
class StreamingHealth:
    """Estado general de salud del subsistema de streaming."""

    captured_at: datetime
    paths: tuple[SRTPathHealth, ...]
    status: HealthStatus
    message: str

    def __post_init__(self) -> None:
        """Valida el estado general del streaming."""

        message = self.message.strip()

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "captured_at debe contener información de zona horaria."
            )

        if not message:
            raise ValueError(
                "El mensaje general debe contener texto válido."
            )

        path_names = tuple(path.name for path in self.paths)

        if len(path_names) != len(set(path_names)):
            raise ValueError(
                "StreamingHealth no admite nombres de paths duplicados."
            )

        object.__setattr__(self, "message", message)

    @classmethod
    def empty(cls, *, captured_at: datetime) -> "StreamingHealth":
        """Construye un estado válido sin métricas SRT."""

        return cls(
            captured_at=captured_at,
            paths=(),
            status=HealthStatus.UNKNOWN,
            message="No existen métricas SRT disponibles.",
        )

    @property
    def path_count(self) -> int:
        """Cantidad de paths evaluados."""

        return len(self.paths)

    @property
    def connection_count(self) -> int:
        """Cantidad total de conexiones SRT evaluadas."""

        return sum(
            path.connection_count
            for path in self.paths
        )

    @property
    def critical_path_count(self) -> int:
        """Cantidad de paths en estado crítico."""

        return sum(
            path.status is HealthStatus.CRITICAL
            for path in self.paths
        )

    @property
    def degraded_path_count(self) -> int:
        """Cantidad de paths degradados."""

        return sum(
            path.status is HealthStatus.DEGRADED
            for path in self.paths
        )

    def get_path(self, name: str) -> SRTPathHealth | None:
        """Busca el estado de salud de un path."""

        return next(
            (
                path
                for path in self.paths
                if path.name == name
            ),
            None,
        )
