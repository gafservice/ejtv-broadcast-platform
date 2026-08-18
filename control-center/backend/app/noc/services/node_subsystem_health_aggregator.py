"""Aggregate subsystem health into integral NodeHealth.

ENG-013B — Node SDK

This service combines canonical NodeHealth values produced by
independent operational subsystems into one integral NodeHealth.

It does not evaluate metrics, network interfaces or alarms.
"""

from __future__ import annotations

from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)


class NodeSubsystemHealthAggregator:
    """Aggregate subsystem health using canonical severity."""

    _SEVERITY = {
        NodeHealthState.HEALTHY: 0,
        NodeHealthState.WARNING: 1,
        NodeHealthState.DEGRADED: 2,
        NodeHealthState.CRITICAL: 3,
    }

    def aggregate(
        self,
        subsystems: tuple[NodeHealth, ...],
    ) -> NodeHealth:
        """Return integral health from subsystem health values."""

        if not isinstance(subsystems, tuple):
            raise TypeError(
                "subsystems must be a tuple"
            )

        for health in subsystems:
            if not isinstance(health, NodeHealth):
                raise TypeError(
                    "subsystems must contain NodeHealth objects"
                )

        if not subsystems:
            return NodeHealth(
                NodeHealthState.UNKNOWN
            )

        known = tuple(
            health
            for health in subsystems
            if health.state is not NodeHealthState.UNKNOWN
        )

        if not known:
            return NodeHealth(
                NodeHealthState.UNKNOWN
            )

        worst = max(
            known,
            key=lambda health: self._severity(
                health.state
            ),
        )

        return NodeHealth(
            worst.state
        )

    @classmethod
    def _severity(
        cls,
        state: NodeHealthState,
    ) -> int:
        """Return ordered severity for a known health state."""

        try:
            return cls._SEVERITY[state]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported NodeHealthState: {state!r}"
            ) from exc
