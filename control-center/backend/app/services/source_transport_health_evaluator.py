"""Evaluate source transport health from path receive evidence.

ENG-013C — Source Transport Health Evaluator v1

This service converts already-derived path transport evidence into the
canonical SourceTransportHealth conclusion for one logical multimedia
signal.

It deliberately does not inspect media evidence, client/delivery
sessions, or protocol-specific transport metrics.
"""

from __future__ import annotations

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.metrics import (
    MeasurementQuality,
    StreamingPathMeasurement,
)
from app.domain.streaming.models import MediaPathStatus
from app.domain.streaming.source_transport_health import (
    SourceTransportHealth,
)


class SourceTransportHealthEvaluator:
    """Evaluate the transport feeding one logical multimedia signal."""

    def evaluate(
        self,
        *,
        service_id: str,
        source_type: str,
        measurement: StreamingPathMeasurement,
    ) -> SourceTransportHealth:
        """Return Source Transport Health without inventing evidence."""

        if not isinstance(measurement, StreamingPathMeasurement):
            raise TypeError(
                "measurement must be a StreamingPathMeasurement"
            )

        status = self._resolve_status(measurement)

        return SourceTransportHealth(
            service_id=service_id,
            path_name=measurement.name,
            source_type=source_type,
            status=status,
        )

    @staticmethod
    def _resolve_status(
        measurement: StreamingPathMeasurement,
    ) -> HealthStatus:
        if measurement.status in (
            MediaPathStatus.OFFLINE,
            MediaPathStatus.NO_SOURCE,
        ):
            return HealthStatus.CRITICAL

        if measurement.quality is not MeasurementQuality.AVAILABLE:
            return HealthStatus.UNKNOWN

        if (
            measurement.inbound_delta_bytes is None
            or measurement.inbound_bitrate_bps is None
        ):
            return HealthStatus.UNKNOWN

        if measurement.inbound_delta_bytes == 0:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY
