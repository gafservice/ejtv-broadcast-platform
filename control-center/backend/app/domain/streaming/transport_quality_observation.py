"""Normalized transport-quality evidence for one multimedia source.

ENG-013C — Transport Quality Observation Contract v1.

This domain object represents observation, not Health evaluation.

It deliberately contains no thresholds, alarms, events, or
protocol-specific metric assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from datetime import datetime, timedelta

from app.domain.sessions.protocol import SessionRole
from app.domain.streaming.evidence_acquisition_interval import EvidenceAcquisitionInterval
from app.domain.streaming.media_observation import EvidenceAvailability


@dataclass(frozen=True, slots=True)
class TransportQualityObservation:
    """Immutable transport-quality evidence identity and availability."""

    service_id: str
    path_name: str
    source_type: str
    observed_at: datetime
    availability: EvidenceAvailability
    metrics: tuple[TransportMetricObservation, ...] = field(
        default_factory=tuple
    )
    acquisition_interval: EvidenceAcquisitionInterval | None = None
    source_id: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "service_id",
            "path_name",
            "source_type",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a str"
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"{field_name} must not be blank"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )

        if self.source_id is not None:
            if not isinstance(self.source_id, str):
                raise TypeError('source_id must be a str')

            normalized_source_id = self.source_id.strip()

            if not normalized_source_id:
                raise ValueError('source_id must not be blank')

            object.__setattr__(
                self,
                'source_id',
                normalized_source_id,
            )

        if not isinstance(self.observed_at, datetime):
            raise TypeError(
                "observed_at must be a datetime"
            )

        if self.observed_at.tzinfo is None:
            raise ValueError(
                "observed_at must be timezone-aware"
            )

        if self.observed_at.utcoffset() != timedelta(0):
            raise ValueError(
                "observed_at must use UTC"
            )

        if not isinstance(
            self.availability,
            EvidenceAvailability,
        ):
            raise TypeError(
                "availability must be EvidenceAvailability"
            )



        if (
            self.acquisition_interval is not None
            and not isinstance(
                self.acquisition_interval,
                EvidenceAcquisitionInterval,
            )
        ):
            raise TypeError(
                'acquisition_interval must be '
                'EvidenceAcquisitionInterval or None'
            )

        if not isinstance(self.metrics, tuple):
            raise TypeError(
                "metrics must be a tuple"
            )

        identities = set()

        for metric in self.metrics:
            if not isinstance(
                metric,
                TransportMetricObservation,
            ):
                raise TypeError(
                    "metrics must contain "
                    "TransportMetricObservation objects"
                )

            identity = (
                metric.metric_name,
                metric.source,
                metric.direction,
                metric.connection_id,
                metric.connection_role,
                metric.measurement_scope,
            )

            if identity in identities:
                raise ValueError(
                    "Duplicate transport metric identity"
                )

            identities.add(identity)


@dataclass(frozen=True, slots=True)
class TransportMetricObservation:
    """Immutable protocol-extensible transport metric evidence."""

    metric_name: str
    value: float | None
    unit: str
    availability: EvidenceAvailability
    source: str
    window_seconds: float | None = None
    direction: str | None = None
    connection_id: str | None = None
    connection_role: SessionRole | None = None
    measurement_scope: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("metric_name", "unit", "source"):
            value = getattr(self, field_name)

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a str"
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"{field_name} must not be blank"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )

        for field_name in ("direction", "connection_id"):
            value = getattr(self, field_name)

            if value is None:
                continue

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a str or None"
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"{field_name} must not be blank"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )

        if (
            self.connection_role is not None
            and not isinstance(self.connection_role, SessionRole)
        ):
            raise TypeError(
                "connection_role must be SessionRole or None"
            )

        if self.measurement_scope is not None:
            if not isinstance(self.measurement_scope, str):
                raise TypeError(
                    "measurement_scope must be str or None"
                )

            normalized_scope = self.measurement_scope.strip()

            if normalized_scope not in (
                "SOURCE",
                "CONNECTION",
                "UNKNOWN",
            ):
                raise ValueError(
                    "Unsupported measurement_scope"
                )

            object.__setattr__(
                self,
                "measurement_scope",
                normalized_scope,
            )

        if not isinstance(
            self.availability,
            EvidenceAvailability,
        ):
            raise TypeError(
                "availability must be EvidenceAvailability"
            )

        if self.value is not None:
            if (
                isinstance(self.value, bool)
                or not isinstance(self.value, (int, float))
            ):
                raise TypeError(
                    "value must be numeric or None"
                )

            if not math.isfinite(self.value):
                raise ValueError(
                    "value must be finite"
                )

        if self.availability is EvidenceAvailability.AVAILABLE:
            if self.value is None:
                raise ValueError(
                    "AVAILABLE metric requires a value"
                )
        elif self.value is not None:
            raise ValueError(
                "Non-available metric must not carry a value"
            )

        if self.window_seconds is not None:
            if (
                isinstance(self.window_seconds, bool)
                or not isinstance(self.window_seconds, (int, float))
            ):
                raise TypeError(
                    "window_seconds must be numeric or None"
                )

            if (
                not math.isfinite(self.window_seconds)
                or self.window_seconds <= 0
            ):
                raise ValueError(
                    "window_seconds must be finite and positive"
                )
