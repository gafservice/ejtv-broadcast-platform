"""Network rate metrics provider for the NOC runtime.

ENG-013B — Node SDK

This infrastructure component translates an already-calculated
NetworkRate into canonical NOC MetricSample objects.

Rate calculation itself remains in the shared system-domain
NetworkRateCalculator.
"""

from __future__ import annotations

from app.domain.system import NetworkRate
from app.noc.domain.node_metric import (
    MetricQuality,
    MetricSample,
)


class NetworkRateMetricsProvider:
    """Translate NetworkRate into current NOC metric samples."""

    def collect(
        self,
        rate: NetworkRate,
    ) -> tuple[MetricSample, ...]:
        """Build RX/TX rate metrics when rates are available."""

        if not isinstance(rate, NetworkRate):
            raise TypeError(
                "rate must be a NetworkRate"
            )

        if (
            rate.rx_bps is None
            or rate.tx_bps is None
        ):
            return ()

        return (
            MetricSample(
                metric="system.network.rx_bps",
                value=rate.rx_bps,
                unit="bps",
                timestamp=rate.captured_at,
                quality=MetricQuality.GOOD,
            ),
            MetricSample(
                metric="system.network.tx_bps",
                value=rate.tx_bps,
                unit="bps",
                timestamp=rate.captured_at,
                quality=MetricQuality.GOOD,
            ),
        )
