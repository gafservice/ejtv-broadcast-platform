"""Shared acquisition of MediaMTX Prometheus evidence.

ENG-013C — Shared Metrics Acquisition Service v1.

One call to acquire() performs one metrics acquisition and one parse.
The result can be reused by multiple downstream consumers.
"""

from __future__ import annotations

from app.adapters.mediamtx.metrics_acquisition import (
    MediaMTXMetricsAcquisition,
)
from app.adapters.mediamtx.metrics_client import (
    MediaMTXMetricsClient,
)
from app.adapters.mediamtx.metrics_parser import (
    MediaMTXMetricsParser,
)


class MediaMTXMetricsAcquisitionService:
    """Acquire and parse one reusable MediaMTX metrics snapshot."""

    def __init__(
        self,
        metrics_client: MediaMTXMetricsClient,
        metrics_parser: MediaMTXMetricsParser,
    ) -> None:
        self._metrics_client = metrics_client
        self._metrics_parser = metrics_parser

    def acquire(self) -> MediaMTXMetricsAcquisition:
        """Acquire one Prometheus document with UTC provenance."""
        metrics_text, interval = (
            self._metrics_client.get_metrics_with_acquisition_interval()
        )

        snapshot = self._metrics_parser.parse(metrics_text)

        return MediaMTXMetricsAcquisition(
            snapshot=snapshot,
            interval=interval,
        )
