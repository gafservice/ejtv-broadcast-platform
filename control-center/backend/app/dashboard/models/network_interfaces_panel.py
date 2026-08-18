"""Modelos de presentación para el panel NETWORK INTERFACES."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class NetworkInterfaceRowData:
    """Información de una interfaz preparada para presentación."""

    interface: str
    interface_type: str

    is_up: bool
    carrier: bool | None

    link_speed_mbps: int | None
    mtu: int

    mac_address: str | None
    ipv4_addresses: tuple[str, ...]
    ipv6_addresses: tuple[str, ...]

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
        """Valida la información preparada para una fila."""

        if not isinstance(self.interface, str) or not self.interface.strip():
            raise ValueError(
                "El nombre de la interfaz debe contener texto válido."
            )

        object.__setattr__(
            self,
            "interface",
            self.interface.strip(),
        )

        if (
            not isinstance(self.interface_type, str)
            or not self.interface_type.strip()
        ):
            raise ValueError(
                "El tipo de interfaz debe contener texto válido."
            )

        object.__setattr__(
            self,
            "interface_type",
            self.interface_type.strip(),
        )

        if not isinstance(self.is_up, bool):
            raise ValueError(
                "El campo 'is_up' debe ser booleano."
            )

        if self.carrier is not None and not isinstance(
            self.carrier,
            bool,
        ):
            raise ValueError(
                "El campo 'carrier' debe ser booleano o None."
            )

        if (
            self.link_speed_mbps is not None
            and (
                isinstance(self.link_speed_mbps, bool)
                or not isinstance(self.link_speed_mbps, int)
                or self.link_speed_mbps < 0
            )
        ):
            raise ValueError(
                "La velocidad del enlace debe ser un entero "
                "mayor o igual que cero o None."
            )

        if (
            isinstance(self.mtu, bool)
            or not isinstance(self.mtu, int)
            or self.mtu <= 0
        ):
            raise ValueError(
                "El MTU debe ser un entero mayor que cero."
            )

        if not isinstance(self.ipv4_addresses, tuple):
            raise ValueError(
                "ipv4_addresses debe ser una tupla."
            )

        if not isinstance(self.ipv6_addresses, tuple):
            raise ValueError(
                "ipv6_addresses debe ser una tupla."
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


@dataclass(frozen=True, slots=True)
class NetworkInterfacesPanelData:
    """Colección de interfaces preparada para el dashboard."""

    interfaces: tuple[NetworkInterfaceRowData, ...]
    captured_at: datetime

    def __post_init__(self) -> None:
        """Valida la colección y su instante de captura."""

        if not isinstance(self.interfaces, tuple):
            raise ValueError(
                "El campo 'interfaces' debe ser una tupla."
            )

        if not all(
            isinstance(item, NetworkInterfaceRowData)
            for item in self.interfaces
        ):
            raise ValueError(
                "Todas las interfaces deben ser "
                "NetworkInterfaceRowData."
            )

        interface_names = tuple(
            item.interface
            for item in self.interfaces
        )

        if len(interface_names) != len(set(interface_names)):
            raise ValueError(
                "No pueden existir interfaces duplicadas."
            )

        if not isinstance(self.captured_at, datetime):
            raise ValueError(
                "El campo 'captured_at' debe contener una fecha válida."
            )

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "El campo 'captured_at' debe incluir zona horaria."
            )
