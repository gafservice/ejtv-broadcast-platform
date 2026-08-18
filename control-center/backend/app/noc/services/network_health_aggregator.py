"""Aggregate effective network-interface health into NodeHealth.

ENG-013B — Node SDK

This service combines the effective operational health of multiple
network interfaces into one canonical NodeHealth value representing
the network subsystem.
"""

from __future__ import annotations

from app.noc.domain.network_interface_health import (
    NetworkInterfaceHealth,
)
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)


class NetworkHealthAggregator:
    """Aggregate interface health using canonical NodeHealth severity."""

    def aggregate(
        self,
        interfaces: tuple[
            NetworkInterfaceHealth,
            ...,
        ],
    ) -> NodeHealth:
        """Return integral health of the network subsystem."""

        if not isinstance(interfaces, tuple):
            raise TypeError(
                "interfaces must be a tuple"
            )

        if not interfaces:
            return NodeHealth(
                NodeHealthState.UNKNOWN
            )

        seen: set[str] = set()
        known_states: list[NodeHealthState] = []

        for interface_health in interfaces:
            if not isinstance(
                interface_health,
                NetworkInterfaceHealth,
            ):
                raise TypeError(
                    "interfaces must contain "
                    "NetworkInterfaceHealth objects"
                )

            interface = interface_health.interface

            if interface in seen:
                raise ValueError(
                    f"Duplicate network interface health: "
                    f"{interface}"
                )

            seen.add(interface)

            if (
                interface_health.state
                is NodeHealthState.UNKNOWN
            ):
                continue

            known_states.append(
                interface_health.state
            )

        if not known_states:
            return NodeHealth(
                NodeHealthState.UNKNOWN
            )

        worst_state = max(
            known_states,
            key=self._severity,
        )

        return NodeHealth(
            worst_state
        )

    @staticmethod
    def _severity(
        state: NodeHealthState,
    ) -> int:
        """Return canonical severity for a known health state."""

        health = NodeHealth(state)

        severity = health.severity

        if severity is None:
            raise ValueError(
                "UNKNOWN health state has no ordered severity"
            )

        return severity
