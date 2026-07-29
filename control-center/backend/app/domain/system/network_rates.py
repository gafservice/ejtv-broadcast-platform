"""Cálculo de tasas de transferencia de una interfaz de red."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.system.models import SystemResources


@dataclass(frozen=True, slots=True)
class NetworkRate:
    """Tasas y contadores actuales de una interfaz de red."""

    interface: str
    rx_bps: float | None
    tx_bps: float | None
    interval_seconds: float | None

    errors_in: int
    errors_out: int
    dropped_in: int
    dropped_out: int

    captured_at: datetime

    def __post_init__(self) -> None:
        """Valida los valores derivados de la medición."""

        if not isinstance(self.interface, str) or not self.interface.strip():
            raise ValueError(
                "La interfaz de red debe contener texto válido."
            )

        object.__setattr__(
            self,
            "interface",
            self.interface.strip(),
        )

        for field_name in ("rx_bps", "tx_bps"):
            value = getattr(self, field_name)

            if value is not None and value < 0:
                raise ValueError(
                    f"El campo '{field_name}' no puede ser negativo."
                )

        if (
            self.interval_seconds is not None
            and self.interval_seconds <= 0
        ):
            raise ValueError(
                "El intervalo debe ser mayor que cero."
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

        if not isinstance(self.captured_at, datetime):
            raise ValueError(
                "El campo 'captured_at' debe contener una fecha válida."
            )

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "El campo 'captured_at' debe incluir zona horaria."
            )


class NetworkRateCalculator:
    """Calcula tasas comparando dos capturas de recursos."""

    def compare(
        self,
        previous: SystemResources | None,
        current: SystemResources,
    ) -> NetworkRate:
        """Calcula RX/TX en bits por segundo."""

        rx_bps: float | None = None
        tx_bps: float | None = None
        interval_seconds: float | None = None

        if previous is not None:
            interval = (
                current.captured_at - previous.captured_at
            ).total_seconds()

            same_interface = (
                previous.network.interface
                == current.network.interface
            )

            received_delta = (
                current.network.bytes_received
                - previous.network.bytes_received
            )

            sent_delta = (
                current.network.bytes_sent
                - previous.network.bytes_sent
            )

            valid_counters = (
                received_delta >= 0
                and sent_delta >= 0
            )

            if interval > 0 and same_interface and valid_counters:
                interval_seconds = interval

                rx_bps = (
                    received_delta * 8.0
                    / interval_seconds
                )

                tx_bps = (
                    sent_delta * 8.0
                    / interval_seconds
                )

        return NetworkRate(
            interface=current.network.interface,
            rx_bps=rx_bps,
            tx_bps=tx_bps,
            interval_seconds=interval_seconds,
            errors_in=current.network.errors_in,
            errors_out=current.network.errors_out,
            dropped_in=current.network.dropped_in,
            dropped_out=current.network.dropped_out,
            captured_at=current.captured_at,
        )
