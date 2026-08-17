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

        samples = [
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
        ]

        quality_rates = (
            (
                "system.network.errors_in_per_second",
                rate.errors_in_per_second,
            ),
            (
                "system.network.errors_out_per_second",
                rate.errors_out_per_second,
            ),
            (
                "system.network.dropped_in_per_second",
                rate.dropped_in_per_second,
            ),
            (
                "system.network.dropped_out_per_second",
                rate.dropped_out_per_second,
            ),
        )

        for metric_name, value in quality_rates:
            if value is None:
                continue

            samples.append(
                MetricSample(
                    metric=metric_name,
                    value=value,
                    unit="count/s",
                    timestamp=rate.captured_at,
                    quality=MetricQuality.GOOD,
                )
            )

        return tuple(samples)
