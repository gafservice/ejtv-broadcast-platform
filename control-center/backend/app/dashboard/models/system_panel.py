"""Modelo agregado de presentación para el panel SYSTEM."""

from dataclasses import dataclass
from datetime import datetime

from app.dashboard.models.cpu_panel import CpuPanelData
from app.dashboard.models.disk_panel import DiskPanelData
from app.dashboard.models.memory_panel import MemoryPanelData
from app.dashboard.models.network_panel import NetworkPanelData
from app.dashboard.models.uptime_panel import UptimePanelData


@dataclass(frozen=True, slots=True)
class SystemPanelData:
    """Conjunto de métricas consumido por el panel SYSTEM."""

    cpu: CpuPanelData
    memory: MemoryPanelData
    disk: DiskPanelData
    network: NetworkPanelData
    uptime: UptimePanelData
    captured_at: datetime

    def __post_init__(self) -> None:
        """Valida la fecha de captura."""

        if not isinstance(self.captured_at, datetime):
            raise ValueError(
                "El campo 'captured_at' debe contener una fecha válida."
            )

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "El campo 'captured_at' debe incluir zona horaria."
            )
