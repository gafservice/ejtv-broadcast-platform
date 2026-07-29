"""Modelo de presentación para el uptime del servidor."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UptimePanelData:
    """Tiempo de actividad preparado para el panel SYSTEM."""

    seconds: float

    def __post_init__(self) -> None:
        """Valida el tiempo de actividad."""

        if self.seconds < 0:
            raise ValueError(
                "El uptime no puede ser negativo."
            )
