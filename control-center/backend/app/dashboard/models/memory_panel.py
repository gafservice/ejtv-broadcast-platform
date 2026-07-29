"""Modelo de presentación para métricas de memoria."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MemoryPanelData:
    """Métricas de memoria preparadas para el panel SYSTEM."""

    usage_percent: float
    used_bytes: int
    total_bytes: int

    def __post_init__(self) -> None:
        """Valida las métricas de memoria."""

        if not 0.0 <= self.usage_percent <= 100.0:
            raise ValueError(
                "El uso de memoria debe estar entre 0 y 100."
            )

        if self.used_bytes < 0:
            raise ValueError(
                "La memoria utilizada no puede ser negativa."
            )

        if self.total_bytes < 0:
            raise ValueError(
                "La memoria total no puede ser negativa."
            )

        if self.used_bytes > self.total_bytes:
            raise ValueError(
                "La memoria utilizada no puede superar la memoria total."
            )
