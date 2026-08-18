"""Diagnostic context for integral NodeHealth.

ENG-013B — Node SDK

NodeHealthDiagnostic preserves the operational evidence used to
produce the integral NodeHealth of a NodeInstance.

It complements NodeHealth but does not alter the canonical NodeHealth
contract and does not represent historical events or alarm lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.noc.domain.network_interface_health import (
    NetworkInterfaceHealth,
)
from app.noc.domain.node_health import NodeHealth


@dataclass(frozen=True, slots=True)
class NodeHealthDiagnostic:
    """Current diagnostic context behind integral NodeHealth."""

    captured_at: datetime

    health: NodeHealth
    system_health: NodeHealth
    network_health: NodeHealth

    network_interfaces: tuple[
        NetworkInterfaceHealth,
        ...,
    ] = ()

    def __post_init__(self) -> None:
        if not isinstance(
            self.captured_at,
            datetime,
        ):
            raise TypeError(
                "captured_at must be a datetime"
            )

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "captured_at must be timezone-aware and UTC"
            )

        offset = self.captured_at.utcoffset()

        if offset is None or offset != timedelta(0):
            raise ValueError(
                "captured_at must be expressed in UTC"
            )

        for name in (
            "health",
            "system_health",
            "network_health",
        ):
            value = getattr(self, name)

            if not isinstance(value, NodeHealth):
                raise TypeError(
                    f"{name} must be a NodeHealth"
                )

        if not isinstance(
            self.network_interfaces,
            tuple,
        ):
            raise TypeError(
                "network_interfaces must be a tuple"
            )

        seen_interfaces: set[str] = set()

        for interface_health in self.network_interfaces:
            if not isinstance(
                interface_health,
                NetworkInterfaceHealth,
            ):
                raise TypeError(
                    "network_interfaces must contain "
                    "NetworkInterfaceHealth values"
                )

            if interface_health.interface in seen_interfaces:
                raise ValueError(
                    "network_interfaces must not contain "
                    "duplicate interfaces"
                )

            seen_interfaces.add(
                interface_health.interface
            )

            if (
                interface_health.observed_at
                != self.captured_at
            ):
                raise ValueError(
                    "network interface observations must "
                    "match diagnostic captured_at"
                )

    @property
    def interface_count(self) -> int:
        """Return the number of diagnosed network interfaces."""

        return len(self.network_interfaces)

    @property
    def unhealthy_interfaces(
        self,
    ) -> tuple[NetworkInterfaceHealth, ...]:
        """Return interfaces requiring operational attention."""

        return tuple(
            interface
            for interface in self.network_interfaces
            if interface.requires_attention
        )
