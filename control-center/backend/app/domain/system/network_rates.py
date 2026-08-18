"""Cálculo de tasas de transferencia de una interfaz de red."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.system.models import NetworkInfo, SystemResources


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

    errors_in_per_second: float | None = None
    errors_out_per_second: float | None = None
    dropped_in_per_second: float | None = None
    dropped_out_per_second: float | None = None

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
    """Calcula tasas comparando capturas de contadores de red."""

    def compare(
        self,
        previous: SystemResources | None,
        current: SystemResources,
    ) -> NetworkRate:
        """Mantiene el cálculo legacy sobre la interfaz primaria."""

        return self.compare_interface(
            previous=(
                previous.network
                if previous is not None
                else None
            ),
            current=current.network,
            previous_captured_at=(
                previous.captured_at
                if previous is not None
                else None
            ),
            current_captured_at=current.captured_at,
        )

    def compare_interface(
        self,
        *,
        previous: NetworkInfo | None,
        current: NetworkInfo,
        previous_captured_at: datetime | None,
        current_captured_at: datetime,
    ) -> NetworkRate:
        """Calcula tasas temporales para una interfaz concreta."""

        if not isinstance(current, NetworkInfo):
            raise TypeError(
                "current must be a NetworkInfo"
            )

        if (
            previous is not None
            and not isinstance(previous, NetworkInfo)
        ):
            raise TypeError(
                "previous must be a NetworkInfo or None"
            )

        if not isinstance(
            current_captured_at,
            datetime,
        ):
            raise TypeError(
                "current_captured_at must be a datetime"
            )

        if current_captured_at.tzinfo is None:
            raise ValueError(
                "current_captured_at must include timezone"
            )

        if (
            previous is not None
            and previous_captured_at is None
        ):
            raise ValueError(
                "previous_captured_at is required "
                "when previous is provided"
            )

        if previous_captured_at is not None:
            if not isinstance(
                previous_captured_at,
                datetime,
            ):
                raise TypeError(
                    "previous_captured_at must be "
                    "a datetime or None"
                )

            if previous_captured_at.tzinfo is None:
                raise ValueError(
                    "previous_captured_at must include timezone"
                )

        rx_bps: float | None = None
        tx_bps: float | None = None
        interval_seconds: float | None = None

        errors_in_per_second: float | None = None
        errors_out_per_second: float | None = None
        dropped_in_per_second: float | None = None
        dropped_out_per_second: float | None = None

        if (
            previous is not None
            and previous_captured_at is not None
        ):
            interval = (
                current_captured_at
                - previous_captured_at
            ).total_seconds()

            same_interface = (
                previous.interface
                == current.interface
            )

            received_delta = (
                current.bytes_received
                - previous.bytes_received
            )

            sent_delta = (
                current.bytes_sent
                - previous.bytes_sent
            )

            valid_counters = (
                received_delta >= 0
                and sent_delta >= 0
            )

            if (
                interval > 0
                and same_interface
                and valid_counters
            ):
                interval_seconds = interval

                rx_bps = (
                    received_delta
                    * 8.0
                    / interval_seconds
                )

                tx_bps = (
                    sent_delta
                    * 8.0
                    / interval_seconds
                )

                quality_deltas = (
                    current.errors_in
                    - previous.errors_in,
                    current.errors_out
                    - previous.errors_out,
                    current.dropped_in
                    - previous.dropped_in,
                    current.dropped_out
                    - previous.dropped_out,
                )

                if all(
                    delta >= 0
                    for delta in quality_deltas
                ):
                    (
                        errors_in_delta,
                        errors_out_delta,
                        dropped_in_delta,
                        dropped_out_delta,
                    ) = quality_deltas

                    errors_in_per_second = (
                        errors_in_delta
                        / interval_seconds
                    )

                    errors_out_per_second = (
                        errors_out_delta
                        / interval_seconds
                    )

                    dropped_in_per_second = (
                        dropped_in_delta
                        / interval_seconds
                    )

                    dropped_out_per_second = (
                        dropped_out_delta
                        / interval_seconds
                    )

        return NetworkRate(
            interface=current.interface,
            rx_bps=rx_bps,
            tx_bps=tx_bps,
            interval_seconds=interval_seconds,
            errors_in=current.errors_in,
            errors_out=current.errors_out,
            dropped_in=current.dropped_in,
            dropped_out=current.dropped_out,
            captured_at=current_captured_at,
            errors_in_per_second=errors_in_per_second,
            errors_out_per_second=errors_out_per_second,
            dropped_in_per_second=dropped_in_per_second,
            dropped_out_per_second=dropped_out_per_second,
        )



class MultiNetworkRateCalculator:
    """Calcula tasas para todas las interfaces presentes actualmente."""

    def __init__(
        self,
        calculator: NetworkRateCalculator | None = None,
    ) -> None:
        self._calculator = (
            calculator
            if calculator is not None
            else NetworkRateCalculator()
        )

    def compare(
        self,
        previous: SystemResources | None,
        current: SystemResources,
    ) -> tuple[NetworkRate, ...]:
        """Calcula tasas por interfaz usando identidad estable."""

        previous_by_interface = (
            {
                network.interface: network
                for network in previous.networks
            }
            if previous is not None
            else {}
        )

        return tuple(
            self._calculator.compare_interface(
                previous=previous_by_interface.get(
                    network.interface
                ),
                current=network,
                previous_captured_at=(
                    previous.captured_at
                    if previous is not None
                    else None
                ),
                current_captured_at=current.captured_at,
            )
            for network in current.networks
        )
