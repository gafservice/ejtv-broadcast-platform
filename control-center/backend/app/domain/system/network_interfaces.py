"""Modelos de dominio para interfaces de red.

ENG-013B — Node SDK

Representa identidad, clasificación y estado operacional de una
interfaz de red sin depender de Linux, psutil ni herramientas externas.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NetworkInterfaceType(str, Enum):
    """Clasificación canónica de una interfaz de red."""

    ETHERNET = "ETHERNET"
    WIFI = "WIFI"
    LOOPBACK = "LOOPBACK"
    BRIDGE = "BRIDGE"
    BOND = "BOND"
    VLAN = "VLAN"
    TUNNEL = "TUNNEL"
    VIRTUAL = "VIRTUAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class NetworkInterfaceInfo:
    """Identidad y estado operacional de una interfaz de red."""

    interface: str
    interface_type: NetworkInterfaceType

    is_up: bool
    carrier: bool | None

    mtu: int

    mac_address: str | None = None
    link_speed_mbps: int | None = None
    duplex: str | None = None

    ipv4_addresses: tuple[str, ...] = ()
    ipv6_addresses: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.interface, str):
            raise TypeError(
                "interface must be a string"
            )

        normalized_interface = self.interface.strip()

        if not normalized_interface:
            raise ValueError(
                "interface must not be empty"
            )

        object.__setattr__(
            self,
            "interface",
            normalized_interface,
        )

        if not isinstance(
            self.interface_type,
            NetworkInterfaceType,
        ):
            raise TypeError(
                "interface_type must be a NetworkInterfaceType"
            )

        if not isinstance(self.is_up, bool):
            raise TypeError(
                "is_up must be a bool"
            )

        if (
            self.carrier is not None
            and not isinstance(self.carrier, bool)
        ):
            raise TypeError(
                "carrier must be a bool or None"
            )

        if (
            isinstance(self.mtu, bool)
            or not isinstance(self.mtu, int)
            or self.mtu <= 0
        ):
            raise ValueError(
                "mtu must be a positive integer"
            )

        if self.link_speed_mbps is not None:
            if (
                isinstance(self.link_speed_mbps, bool)
                or not isinstance(
                    self.link_speed_mbps,
                    int,
                )
                or self.link_speed_mbps < 0
            ):
                raise ValueError(
                    "link_speed_mbps must be a non-negative "
                    "integer or None"
                )

        if self.mac_address is not None:
            if not isinstance(
                self.mac_address,
                str,
            ):
                raise TypeError(
                    "mac_address must be a string or None"
                )

            normalized_mac = self.mac_address.strip()

            object.__setattr__(
                self,
                "mac_address",
                normalized_mac or None,
            )

        if self.duplex is not None:
            if not isinstance(self.duplex, str):
                raise TypeError(
                    "duplex must be a string or None"
                )

            normalized_duplex = self.duplex.strip()

            object.__setattr__(
                self,
                "duplex",
                normalized_duplex or None,
            )

        for field_name in (
            "ipv4_addresses",
            "ipv6_addresses",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, tuple):
                raise TypeError(
                    f"{field_name} must be a tuple"
                )

            normalized = tuple(
                address.strip()
                for address in value
                if isinstance(address, str)
                and address.strip()
            )

            if len(normalized) != len(value):
                raise ValueError(
                    f"{field_name} must contain only "
                    "non-empty strings"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )
