"""Servicio de aplicación para telemetría de interfaces de red.

ENG-013B — Node SDK

Coordina identidad, estado, contadores y tasas de las interfaces
sin introducir dependencias de Linux en el dominio.
"""

from __future__ import annotations

from app.domain.system import (
    MultiNetworkRateCalculator,
    NetworkInterfaceInfo,
    NetworkInterfaceTelemetry,
    SystemResources,
)


class NetworkTelemetryService:
    """Construye telemetría consolidada para múltiples interfaces."""

    def __init__(
        self,
        rate_calculator: MultiNetworkRateCalculator | None = None,
    ) -> None:
        self._rate_calculator = (
            rate_calculator
            if rate_calculator is not None
            else MultiNetworkRateCalculator()
        )

    def build(
        self,
        *,
        previous: SystemResources | None,
        current: SystemResources,
        interface_infos: tuple[NetworkInterfaceInfo, ...],
    ) -> tuple[NetworkInterfaceTelemetry, ...]:
        """Construye la telemetría de las interfaces actuales."""

        if not isinstance(current, SystemResources):
            raise TypeError(
                "current must be a SystemResources"
            )

        if (
            previous is not None
            and not isinstance(previous, SystemResources)
        ):
            raise TypeError(
                "previous must be a SystemResources or None"
            )

        if not isinstance(interface_infos, tuple):
            raise TypeError(
                "interface_infos must be a tuple"
            )

        info_by_interface = {
            info.interface: info
            for info in interface_infos
        }

        counters_by_interface = {
            counters.interface: counters
            for counters in current.networks
        }

        rates = self._rate_calculator.compare(
            previous,
            current,
        )

        rates_by_interface = {
            rate.interface: rate
            for rate in rates
        }

        telemetry: list[NetworkInterfaceTelemetry] = []

        for counters in current.networks:
            interface = counters.interface

            info = info_by_interface.get(interface)

            if info is None:
                raise ValueError(
                    "Missing NetworkInterfaceInfo for "
                    f"interface '{interface}'"
                )

            telemetry.append(
                NetworkInterfaceTelemetry(
                    info=info,
                    counters=counters_by_interface[interface],
                    captured_at=current.captured_at,
                    rates=rates_by_interface.get(interface),
                )
            )

        return tuple(telemetry)
