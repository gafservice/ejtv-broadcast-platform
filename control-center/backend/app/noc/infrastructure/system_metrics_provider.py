"""System resource metrics provider for the NOC runtime.

ENG-013B — Node SDK

This infrastructure component translates the existing SystemResources
application model into canonical NOC MetricSample objects.

Metric calculation remains outside the NOC domain. The NOC receives
already-observed operational values through MetricSample.
"""

from __future__ import annotations

from app.domain.system import SystemResources
from app.noc.domain.node_metric import (
    MetricQuality,
    MetricSample,
)


class SystemMetricsProvider:
    """Translate SystemResources into current NOC metric samples."""

    def collect(
        self,
        resources: SystemResources,
    ) -> tuple[MetricSample, ...]:
        """Build canonical metric samples from one system capture."""

        if not isinstance(resources, SystemResources):
            raise TypeError(
                "resources must be a SystemResources"
            )

        timestamp = resources.captured_at

        return (
            MetricSample(
                metric="system.cpu.usage_percent",
                value=resources.cpu.usage_percent,
                unit="%",
                timestamp=timestamp,
                quality=MetricQuality.GOOD,
            ),
            MetricSample(
                metric="system.memory.usage_percent",
                value=resources.memory.usage_percent,
                unit="%",
                timestamp=timestamp,
                quality=MetricQuality.GOOD,
            ),
            MetricSample(
                metric="system.disk.usage_percent",
                value=resources.disk.usage_percent,
                unit="%",
                timestamp=timestamp,
                quality=MetricQuality.GOOD,
            ),
            MetricSample(
                metric="system.network.rx_bytes",
                value=resources.network.bytes_received,
                unit="bytes",
                timestamp=timestamp,
                quality=MetricQuality.GOOD,
            ),
            MetricSample(
                metric="system.network.tx_bytes",
                value=resources.network.bytes_sent,
                unit="bytes",
                timestamp=timestamp,
                quality=MetricQuality.GOOD,
            ),
            MetricSample(
                metric="system.uptime_seconds",
                value=resources.uptime.uptime_seconds,
                unit="s",
                timestamp=timestamp,
                quality=MetricQuality.GOOD,
            ),
        )
