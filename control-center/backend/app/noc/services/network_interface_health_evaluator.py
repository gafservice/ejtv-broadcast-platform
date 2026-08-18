"""Health evaluation for network interfaces.

ENG-013B — Node SDK

Transforms operational network telemetry into a canonical health
evaluation without creating alarms or applying interface-role policy.
"""

from __future__ import annotations

from app.domain.system import NetworkInterfaceTelemetry
from app.noc.domain.network_interface_health import (
    NetworkInterfaceHealth,
)
from app.noc.domain.node_health import NodeHealthState


class NetworkInterfaceHealthEvaluator:
    """Evaluates the operational health of one network interface."""

    WARNING_RATE = 1.0
    DEGRADED_RATE = 10.0

    def evaluate(
        self,
        telemetry: NetworkInterfaceTelemetry,
    ) -> NetworkInterfaceHealth:
        """Evaluate one interface from its current telemetry."""

        if not isinstance(
            telemetry,
            NetworkInterfaceTelemetry,
        ):
            raise TypeError(
                "telemetry must be a NetworkInterfaceTelemetry"
            )

        info = telemetry.info
        rates = telemetry.rates

        # ---------------------------------------------------------
        # Interface administratively / operationally down.
        #
        # Without role policy we cannot know whether this interface
        # is expected to be active, so DOWN is not automatically a
        # failure.
        # ---------------------------------------------------------

        if not info.is_up:
            return NetworkInterfaceHealth(
                interface=info.interface,
                state=NodeHealthState.UNKNOWN,
                observed_at=telemetry.captured_at,
                reason="Interface is down; expected role is unknown",
                carrier_ok=info.carrier,
                traffic_ok=None,
                error_rate=None,
                drop_rate=None,
            )

        # ---------------------------------------------------------
        # Interface is UP but physical carrier is absent.
        # ---------------------------------------------------------

        if info.carrier is False:
            return NetworkInterfaceHealth(
                interface=info.interface,
                state=NodeHealthState.CRITICAL,
                observed_at=telemetry.captured_at,
                reason="Interface is up but carrier is absent",
                carrier_ok=False,
                traffic_ok=None,
                error_rate=None,
                drop_rate=None,
            )

        # ---------------------------------------------------------
        # No temporal rates yet.
        #
        # This is expected during the first capture.
        # ---------------------------------------------------------

        if rates is None or rates.interval_seconds is None:
            return NetworkInterfaceHealth(
                interface=info.interface,
                state=NodeHealthState.UNKNOWN,
                observed_at=telemetry.captured_at,
                reason="Insufficient samples to calculate network rates",
                carrier_ok=info.carrier,
                traffic_ok=None,
                error_rate=None,
                drop_rate=None,
            )

        error_rate = self._sum_rates(
            rates.errors_in_per_second,
            rates.errors_out_per_second,
        )

        drop_rate = self._sum_rates(
            rates.dropped_in_per_second,
            rates.dropped_out_per_second,
        )

        traffic_ok = (
            rates.rx_bps is not None
            and rates.tx_bps is not None
        )

        # ---------------------------------------------------------
        # A counter reset or unavailable quality delta can make the
        # derived quality rates unavailable even when throughput was
        # successfully calculated.
        # ---------------------------------------------------------

        if error_rate is None or drop_rate is None:
            return NetworkInterfaceHealth(
                interface=info.interface,
                state=NodeHealthState.UNKNOWN,
                observed_at=telemetry.captured_at,
                reason="Network quality rates are unavailable",
                carrier_ok=info.carrier,
                traffic_ok=traffic_ok,
                error_rate=error_rate,
                drop_rate=drop_rate,
            )

        worst_rate = max(
            error_rate,
            drop_rate,
        )

        if worst_rate >= self.DEGRADED_RATE:
            return NetworkInterfaceHealth(
                interface=info.interface,
                state=NodeHealthState.DEGRADED,
                observed_at=telemetry.captured_at,
                reason="High network error or drop rate",
                carrier_ok=info.carrier,
                traffic_ok=traffic_ok,
                error_rate=error_rate,
                drop_rate=drop_rate,
            )

        if worst_rate >= self.WARNING_RATE:
            return NetworkInterfaceHealth(
                interface=info.interface,
                state=NodeHealthState.WARNING,
                observed_at=telemetry.captured_at,
                reason="Elevated network error or drop rate",
                carrier_ok=info.carrier,
                traffic_ok=traffic_ok,
                error_rate=error_rate,
                drop_rate=drop_rate,
            )

        return NetworkInterfaceHealth(
            interface=info.interface,
            state=NodeHealthState.HEALTHY,
            observed_at=telemetry.captured_at,
            reason="Interface operating normally",
            carrier_ok=info.carrier,
            traffic_ok=traffic_ok,
            error_rate=error_rate,
            drop_rate=drop_rate,
        )

    @staticmethod
    def _sum_rates(
        inbound: float | None,
        outbound: float | None,
    ) -> float | None:
        """Combine RX/TX quality rates when both are available."""

        if inbound is None or outbound is None:
            return None

        return inbound + outbound
