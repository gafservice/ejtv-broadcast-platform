"""Telemetría consolidada de interfaces de red.

ENG-013B — Node SDK

Compone identidad, estado, contadores y tasas de una interfaz
sin depender de Linux ni de mecanismos concretos de adquisición.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.system.models import NetworkInfo
from app.domain.system.network_interfaces import (
    NetworkInterfaceInfo,
)
from app.domain.system.network_rates import NetworkRate


@dataclass(frozen=True, slots=True)
class NetworkInterfaceTelemetry:
    """Telemetría operacional consolidada de una interfaz."""

    info: NetworkInterfaceInfo
    counters: NetworkInfo
    rates: NetworkRate | None = None

    def __post_init__(self) -> None:
        """Valida tipos y coherencia de identidad."""

        if not isinstance(
            self.info,
            NetworkInterfaceInfo,
        ):
            raise TypeError(
                "info must be a NetworkInterfaceInfo"
            )

        if not isinstance(
            self.counters,
            NetworkInfo,
        ):
            raise TypeError(
                "counters must be a NetworkInfo"
            )

        if (
            self.rates is not None
            and not isinstance(
                self.rates,
                NetworkRate,
            )
        ):
            raise TypeError(
                "rates must be a NetworkRate or None"
            )

        interface = self.info.interface

        if self.counters.interface != interface:
            raise ValueError(
                "info and counters must refer to "
                "the same interface"
            )

        if (
            self.rates is not None
            and self.rates.interface != interface
        ):
            raise ValueError(
                "info, counters and rates must refer "
                "to the same interface"
            )

    @property
    def interface(self) -> str:
        """Retorna la identidad canónica de la interfaz."""

        return self.info.interface
