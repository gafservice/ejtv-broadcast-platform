"""Operational policy for network interfaces.

ENG-013B — Node SDK

Defines the intended operational role and expectations of one network
interface. Policy is declarative: it does not evaluate telemetry,
create alarms or alter interface state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NetworkInterfaceRole(str, Enum):
    """Canonical operational roles for network interfaces."""

    INGEST = "INGEST"
    PUBLICATION = "PUBLICATION"
    MANAGEMENT = "MANAGEMENT"
    BACKUP = "BACKUP"
    TEST = "TEST"
    LOOPBACK = "LOOPBACK"
    OTHER = "OTHER"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(
        cls,
        value: str,
    ) -> "NetworkInterfaceRole":
        if not isinstance(value, str):
            raise TypeError(
                "NetworkInterfaceRole value must be a string"
            )

        normalized = value.strip().upper()

        if not normalized:
            raise ValueError(
                "NetworkInterfaceRole value must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported NetworkInterfaceRole: {value!r}"
            ) from exc


@dataclass(frozen=True, slots=True)
class NetworkInterfacePolicy:
    """Declared operational policy for one network interface."""

    interface: str
    role: NetworkInterfaceRole

    expected_up: bool = True
    critical: bool = False

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
            self.role,
            NetworkInterfaceRole,
        ):
            raise TypeError(
                "role must be a NetworkInterfaceRole"
            )

        if not isinstance(self.expected_up, bool):
            raise TypeError(
                "expected_up must be a bool"
            )

        if not isinstance(self.critical, bool):
            raise TypeError(
                "critical must be a bool"
            )

    @property
    def is_required(self) -> bool:
        """Return whether the interface is expected to be operational."""

        return self.expected_up

    @property
    def is_optional(self) -> bool:
        """Return whether the interface may normally remain down."""

        return not self.expected_up
