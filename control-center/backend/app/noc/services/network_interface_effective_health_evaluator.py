"""Policy-aware health evaluation for network interfaces.

ENG-013B — Node SDK

Combines observed interface health with declared operational policy.
It does not create events or alarms.
"""

from __future__ import annotations

from app.noc.domain.network_interface_health import (
    NetworkInterfaceHealth,
)
from app.noc.domain.network_interface_policy import (
    NetworkInterfacePolicy,
)
from app.noc.domain.node_health import NodeHealthState


class NetworkInterfaceEffectiveHealthEvaluator:
    """Applies interface policy to observed operational health."""

    def evaluate(
        self,
        observed: NetworkInterfaceHealth,
        policy: NetworkInterfacePolicy,
    ) -> NetworkInterfaceHealth:
        """Return effective health after applying interface policy."""

        if not isinstance(
            observed,
            NetworkInterfaceHealth,
        ):
            raise TypeError(
                "observed must be a NetworkInterfaceHealth"
            )

        if not isinstance(
            policy,
            NetworkInterfacePolicy,
        ):
            raise TypeError(
                "policy must be a NetworkInterfacePolicy"
            )

        if observed.interface != policy.interface:
            raise ValueError(
                "observed health and policy must refer "
                "to the same interface"
            )

        # Known observed failures remain authoritative.
        if observed.state is not NodeHealthState.UNKNOWN:
            return observed

        # Optional interface:
        # DOWN / unknown can be normal by declared policy.
        if policy.is_optional:
            return self._copy_with(
                observed,
                state=NodeHealthState.HEALTHY,
                reason=(
                    "Optional interface is not required "
                    "to be operational"
                ),
            )

        # UNKNOWN is not automatically a failure.
        #
        # A required interface may be UNKNOWN simply because temporal
        # quality rates are not available yet. Only explicit physical
        # evidence of missing carrier is sufficient to promote UNKNOWN
        # into an operational failure.
        if observed.carrier_ok is not False:
            return observed

        # Required + critical interface with explicit carrier failure.
        if policy.critical:
            return self._copy_with(
                observed,
                state=NodeHealthState.CRITICAL,
                reason=(
                    "Required critical interface is not "
                    "operational"
                ),
            )

        # Required but non-critical interface with explicit carrier
        # failure.
        return self._copy_with(
            observed,
            state=NodeHealthState.DEGRADED,
            reason=(
                "Required interface is not operational"
            ),
        )

    @staticmethod
    def _copy_with(
        observed: NetworkInterfaceHealth,
        *,
        state: NodeHealthState,
        reason: str,
    ) -> NetworkInterfaceHealth:
        """Preserve evidence while replacing effective state."""

        return NetworkInterfaceHealth(
            interface=observed.interface,
            state=state,
            observed_at=observed.observed_at,
            reason=reason,
            carrier_ok=observed.carrier_ok,
            traffic_ok=observed.traffic_ok,
            error_rate=observed.error_rate,
            drop_rate=observed.drop_rate,
        )
