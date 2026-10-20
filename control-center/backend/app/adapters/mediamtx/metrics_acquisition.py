"""Immutable shared acquisition of parsed MediaMTX metrics.

ENG-013C — Shared Metrics Acquisition Contract v1.

This object carries already acquired evidence. It does not perform
HTTP requests, evaluate Health, or infer transport quality.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.adapters.mediamtx.metrics_parser import (
    MediaMTXMetricsSnapshot,
)
from app.domain.streaming.evidence_acquisition_interval import (
    EvidenceAcquisitionInterval,
)


@dataclass(frozen=True, slots=True)
class MediaMTXMetricsAcquisition:
    """Parsed Prometheus snapshot with its acquisition provenance."""

    snapshot: MediaMTXMetricsSnapshot
    interval: EvidenceAcquisitionInterval

    def __post_init__(self) -> None:
        if not isinstance(
            self.snapshot,
            MediaMTXMetricsSnapshot,
        ):
            raise TypeError(
                "snapshot must be MediaMTXMetricsSnapshot"
            )

        if not isinstance(
            self.interval,
            EvidenceAcquisitionInterval,
        ):
            raise TypeError(
                "interval must be EvidenceAcquisitionInterval"
            )
