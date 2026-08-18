"""Modelos de presentación utilizados por el dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.streaming import StreamingHealth
from app.dashboard.models.network_interfaces_panel import NetworkInterfacesPanelData
from app.dashboard.models.node_health_panel import NodeHealthPanelData
from app.dashboard.models.system_panel import SystemPanelData
from app.dashboard.models.session_panel import SessionPanelData
from app.dashboard.models.active_connections_panel import (
    ActiveConnectionsPanelData,
)


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
    """Datos completos requeridos para renderizar el dashboard."""

    server: ServerPanelData
    streaming: StreamingPanelData
    paths: tuple[PathRowData, ...]

    sessions: SessionPanelData | None = None
    active_connections: ActiveConnectionsPanelData | None = None
    system: SystemPanelData | None = None
    health: StreamingHealth | None = None
    network_interfaces: NetworkInterfacesPanelData | None = None
    node_health: NodeHealthPanelData | None = None