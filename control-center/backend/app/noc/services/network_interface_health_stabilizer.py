"""Temporal stabilization of effective network-interface health.

ENG-013B — Node SDK

This service prevents short-lived interface-health fluctuations from
immediately propagating into the integral network and Node health.

CRITICAL transitions remain immediate. Other state changes must remain
stable for a configurable amount of time before they are committed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.noc.domain.network_interface_health import (
    NetworkInterfaceHealth,
)
from app.noc.domain.node_health import NodeHealthState


@dataclass(slots=True)
class _InterfaceStabilizationState:
    """Internal temporal state for one network interface."""

    stable: NetworkInterfaceHealth
    candidate: NetworkInterfaceHealth | None = None
    candidate_since: datetime | None = None


class NetworkInterfaceHealthStabilizer:
    """Apply temporal hysteresis to effective interface health."""

    def __init__(
        self,
        *,
        degradation_seconds: float = 3.0,
        recovery_seconds: float = 5.0,
    ) -> None:
        if isinstance(degradation_seconds, bool) or not isinstance(
            degradation_seconds,
            (int, float),
        ):
            raise TypeError(
                "degradation_seconds must be a number"
            )

        if isinstance(recovery_seconds, bool) or not isinstance(
            recovery_seconds,
            (int, float),
        ):
            raise TypeError(
                "recovery_seconds must be a number"
            )

        if degradation_seconds < 0:
            raise ValueError(
                "degradation_seconds must not be negative"
            )

        if recovery_seconds < 0:
            raise ValueError(
                "recovery_seconds must not be negative"
            )

        self._degradation_delay = timedelta(
            seconds=float(degradation_seconds)
        )
        self._recovery_delay = timedelta(
            seconds=float(recovery_seconds)
        )

        self._states: dict[
            str,
            _InterfaceStabilizationState,
        ] = {}

    def stabilize(
        self,
        health: NetworkInterfaceHealth,
    ) -> NetworkInterfaceHealth:
        """Return the temporally stabilized interface health."""

        if not isinstance(
            health,
            NetworkInterfaceHealth,
        ):
            raise TypeError(
                "health must be a NetworkInterfaceHealth"
            )

        interface = health.interface
        state = self._states.get(interface)

        if state is None:
            self._states[interface] = (
                _InterfaceStabilizationState(
                    stable=health,
                )
            )
            return health

        stable = state.stable

        if health.observed_at < stable.observed_at:
            raise ValueError(
                "interface health observations must not "
                "move backwards in time"
            )

        if health.state is stable.state:
            state.stable = health
            state.candidate = None
            state.candidate_since = None
            return health

        if health.state is NodeHealthState.CRITICAL:
            state.stable = health
            state.candidate = None
            state.candidate_since = None
            return health

        if (
            state.candidate is None
            or state.candidate.state is not health.state
        ):
            state.candidate = health
            state.candidate_since = health.observed_at

            if self._required_delay(
                stable.state,
                health.state,
            ) == timedelta(0):
                state.stable = health
                state.candidate = None
                state.candidate_since = None
                return health

            return self._hold_stable_state(
                current=health,
                stable_state=stable.state,
            )

        candidate_since = state.candidate_since

        if candidate_since is None:
            raise RuntimeError(
                "candidate_since missing for active candidate"
            )

        state.candidate = health

        required_delay = self._required_delay(
            stable.state,
            health.state,
        )

        if (
            health.observed_at - candidate_since
            >= required_delay
        ):
            state.stable = health
            state.candidate = None
            state.candidate_since = None
            return health

        return self._hold_stable_state(
            current=health,
            stable_state=stable.state,
        )

    def reset(
        self,
        interface: str | None = None,
    ) -> None:
        """Forget stabilization history for one or all interfaces."""

        if interface is None:
            self._states.clear()
            return

        if not isinstance(interface, str):
            raise TypeError(
                "interface must be a string or None"
            )

        normalized = interface.strip()

        if not normalized:
            raise ValueError(
                "interface must not be empty"
            )

        self._states.pop(
            normalized,
            None,
        )

    @staticmethod
    def _hold_stable_state(
        *,
        current: NetworkInterfaceHealth,
        stable_state: NodeHealthState,
    ) -> NetworkInterfaceHealth:
        """Hold stable state while preserving current evidence.

        Temporal stabilization retains the committed health state,
        but timestamp and diagnostic evidence always belong to the
        current observation cycle.
        """

        return NetworkInterfaceHealth(
            interface=current.interface,
            state=stable_state,
            observed_at=current.observed_at,
            reason=(
                f"Temporally stabilized at {stable_state.value}; "
                f"current observation: {current.reason}"
            ),
            carrier_ok=current.carrier_ok,
            traffic_ok=current.traffic_ok,
            error_rate=current.error_rate,
            drop_rate=current.drop_rate,
        )

    def _required_delay(
        self,
        previous: NodeHealthState,
        current: NodeHealthState,
    ) -> timedelta:
        """Return temporal confirmation required for a transition."""

        if current is NodeHealthState.CRITICAL:
            return timedelta(0)

        previous_severity = self._severity(previous)
        current_severity = self._severity(current)

        if (
            previous_severity is None
            or current_severity is None
        ):
            return self._degradation_delay

        if current_severity > previous_severity:
            return self._degradation_delay

        return self._recovery_delay

    @staticmethod
    def _severity(
        state: NodeHealthState,
    ) -> int | None:
        if state is NodeHealthState.UNKNOWN:
            return None

        return {
            NodeHealthState.HEALTHY: 0,
            NodeHealthState.WARNING: 1,
            NodeHealthState.DEGRADED: 2,
            NodeHealthState.CRITICAL: 3,
        }[state]
