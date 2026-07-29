"""Modelo de presentación para métricas de disco."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiskPanelData:
    """Métricas de disco preparadas para el panel SYSTEM."""

    usage_percent: float
    used_bytes: int
    total_bytes: int

    def __post_init__(self) -> None:
        """Valida las métricas de disco."""

        if not 0.0 <= self.usage_percent <= 100.0:
            raise ValueError(
                "El uso de disco debe estar entre 0 y 100."
            )

        if self.used_bytes < 0:
            raise ValueError(
                "El espacio utilizado no puede ser negativo."
            )

        if self.total_bytes < 0:
            raise ValueError(
                "El espacio total no puede ser negativo."
            )

        if self.used_bytes > self.total_bytes:
            raise ValueError(
                "El espacio utilizado no puede superar el espacio total."
            )
