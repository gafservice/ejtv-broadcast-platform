"""Modelo de presentación para métricas de red."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NetworkPanelData:
    """Métricas de red preparadas para el panel SYSTEM."""

    interface: str

    rx_bps: float | None
    tx_bps: float | None

    errors_in: int
    errors_out: int

    dropped_in: int
    dropped_out: int

    errors_in_per_second: float | None = None
    errors_out_per_second: float | None = None
    dropped_in_per_second: float | None = None
    dropped_out_per_second: float | None = None

    def __post_init__(self) -> None:
        """Valida las métricas de red."""

        if not isinstance(self.interface, str) or not self.interface.strip():
            raise ValueError(
                "La interfaz de red debe contener texto válido."
            )

        object.__setattr__(
            self,
            "interface",
            self.interface.strip(),
        )

        for field_name in (
            "rx_bps",
            "tx_bps",
            "errors_in_per_second",
            "errors_out_per_second",
            "dropped_in_per_second",
            "dropped_out_per_second",
        ):
            value = getattr(self, field_name)

            if value is not None and value < 0:
                raise ValueError(
                    f"El campo '{field_name}' no puede ser negativo."
                )

        for field_name in (
            "errors_in",
            "errors_out",
            "dropped_in",
            "dropped_out",
        ):
            value = getattr(self, field_name)

            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(
                    f"El campo '{field_name}' debe ser un entero."
                )

            if value < 0:
                raise ValueError(
                    f"El campo '{field_name}' no puede ser negativo."
                )
