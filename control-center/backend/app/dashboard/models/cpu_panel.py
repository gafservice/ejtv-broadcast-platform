"""Modelo de presentación para métricas de CPU."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CpuPanelData:
    """Métricas de CPU preparadas para el panel SYSTEM."""

    usage_percent: float
    per_core_usage_percent: tuple[float, ...]
    logical_cores: int
    physical_cores: int | None
    frequency_mhz: float | None

    def __post_init__(self) -> None:
        """Valida las métricas de CPU."""

        if not 0.0 <= self.usage_percent <= 100.0:
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

        if self.frequency_mhz is not None and self.frequency_mhz < 0:
            raise ValueError(
                "La frecuencia de CPU no puede ser negativa."
            )
