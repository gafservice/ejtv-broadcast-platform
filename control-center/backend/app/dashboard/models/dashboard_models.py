"""Modelos de presentación utilizados por el dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.streaming import StreamingHealth


@dataclass(frozen=True, slots=True)
class ServerPanelData:
    """Información mostrada en el panel SERVER."""

    hostname: str
    mediamtx_online: bool
    api_online: bool
    snapshot_at: datetime | None
    quality: str


@dataclass(frozen=True, slots=True)
class StreamingPanelData:
    """Resumen general mostrado en el panel STREAMING."""

    active_paths: int
    readers: int
    inbound_bitrate_bps: float | None
    outbound_bitrate_bps: float | None
    quality: str

    def __post_init__(self) -> None:
        """Valida que el resumen contenga valores coherentes."""

        if self.active_paths < 0:
            raise ValueError(
                "La cantidad de paths activos no puede ser negativa."
            )

        if self.readers < 0:
            raise ValueError(
                "La cantidad de lectores no puede ser negativa."
            )


@dataclass(frozen=True, slots=True)
class SystemPanelData:
    """Recursos del servidor mostrados en el panel SYSTEM."""

    cpu_usage_percent: float
    per_core_usage_percent: tuple[float, ...]
    logical_cores: int
    physical_cores: int | None
    frequency_mhz: float | None

    memory_usage_percent: float
    memory_used_bytes: int
    memory_total_bytes: int

    disk_usage_percent: float
    disk_used_bytes: int
    disk_total_bytes: int

    uptime_seconds: float

    network_interface: str
    network_bytes_sent: int
    network_bytes_received: int
    network_errors_in: int
    network_errors_out: int
    network_dropped_in: int
    network_dropped_out: int

    captured_at: datetime

    def __post_init__(self) -> None:
        """Valida que las métricas del sistema sean coherentes."""

        if not 0.0 <= self.cpu_usage_percent <= 100.0:
            raise ValueError(
                "El uso total de CPU debe estar entre 0 y 100."
            )

        if any(
            usage < 0.0 or usage > 100.0
            for usage in self.per_core_usage_percent
        ):
            raise ValueError(
                "El uso de cada núcleo debe estar entre 0 y 100."
            )

        if self.logical_cores <= 0:
            raise ValueError(
                "La cantidad de núcleos lógicos debe ser positiva."
            )

        if (
            self.physical_cores is not None
            and self.physical_cores <= 0
        ):
            raise ValueError(
                "La cantidad de núcleos físicos debe ser positiva."
            )

        if not 0.0 <= self.memory_usage_percent <= 100.0:
            raise ValueError(
                "El uso de memoria debe estar entre 0 y 100."
            )

        if not 0.0 <= self.disk_usage_percent <= 100.0:
            raise ValueError(
                "El uso de disco debe estar entre 0 y 100."
            )

        if self.memory_used_bytes < 0:
            raise ValueError(
                "La memoria utilizada no puede ser negativa."
            )

        if self.memory_total_bytes < 0:
            raise ValueError(
                "La memoria total no puede ser negativa."
            )

        if self.disk_used_bytes < 0:
            raise ValueError(
                "El espacio utilizado no puede ser negativo."
            )

        if self.disk_total_bytes < 0:
            raise ValueError(
                "El espacio total no puede ser negativo."
            )

        if self.uptime_seconds < 0:
            raise ValueError(
                "El uptime no puede ser negativo."
            )

        if (
            not isinstance(self.network_interface, str)
            or not self.network_interface.strip()
        ):
            raise ValueError(
                "La interfaz de red debe contener texto válido."
            )

        object.__setattr__(
            self,
            "network_interface",
            self.network_interface.strip(),
        )


@dataclass(frozen=True, slots=True)
class PathRowData:
    """Información preparada para una fila de la tabla de paths."""

    name: str
    status: str
    readers: int
    inbound_bitrate_bps: float | None
    outbound_bitrate_bps: float | None
    quality: str
    source: str

    def __post_init__(self) -> None:
        """Valida la información mínima requerida por una fila."""

        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(
                "El nombre del path debe contener texto válido."
            )

        if self.readers < 0:
            raise ValueError(
                "La cantidad de lectores no puede ser negativa."
            )

        object.__setattr__(self, "name", self.name.strip())


@dataclass(frozen=True, slots=True)
class DashboardData:
    """Conjunto completo de información consumido por el dashboard."""

    server: ServerPanelData
    streaming: StreamingPanelData
    paths: tuple[PathRowData, ...]

    system: SystemPanelData | None = None
    health: StreamingHealth | None = None
