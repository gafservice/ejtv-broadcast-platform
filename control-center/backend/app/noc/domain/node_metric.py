"""Operational metric samples published by a NodeInstance.

ENG-013B — Node SDK
NCS reference: 16-NODE-METRIC.md
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from math import isfinite
from numbers import Real


MetricValue = int | float


class MetricQuality(str, Enum):
    """Canonical MetricSample quality values defined by NCS v1.0.0."""

    GOOD = "GOOD"
    DEGRADED = "DEGRADED"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(cls, value: str) -> "MetricQuality":
        if not isinstance(value, str):
            raise TypeError(
                "MetricQuality value must be a string"
            )

        normalized = value.strip().upper()

        if not normalized:
            raise ValueError(
                "MetricQuality value must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported MetricQuality: {value!r}"
            ) from exc


@dataclass(frozen=True, slots=True)
class MetricSample:
    """Single observation of an operational variable."""

    metric: str
    value: MetricValue
    unit: str
    timestamp: datetime
    quality: MetricQuality = MetricQuality.GOOD

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metric",
            self._normalize_required_string(
                self.metric,
                "metric",
            ),
        )

        object.__setattr__(
            self,
            "unit",
            self._normalize_required_string(
                self.unit,
                "unit",
            ),
        )

        if isinstance(self.value, bool) or not isinstance(
            self.value,
            Real,
        ):
            raise TypeError(
                "MetricSample.value must be a real number"
            )

        if not isfinite(float(self.value)):
            raise ValueError(
                "MetricSample.value must be finite"
            )

        if not isinstance(self.timestamp, datetime):
            raise TypeError(
                "MetricSample.timestamp must be a datetime"
            )

        if self.timestamp.tzinfo is None:
            raise ValueError(
                "MetricSample.timestamp must be timezone-aware and UTC"
            )

        offset = self.timestamp.utcoffset()

        if offset is None or offset != timedelta(0):
            raise ValueError(
                "MetricSample.timestamp must be expressed in UTC"
            )

        if not isinstance(self.quality, MetricQuality):
            raise TypeError(
                "MetricSample.quality must be a MetricQuality"
            )

    @property
    def is_good(self) -> bool:
        return self.quality is MetricQuality.GOOD

    @property
    def is_degraded(self) -> bool:
        return self.quality is MetricQuality.DEGRADED

    @property
    def is_invalid(self) -> bool:
        return self.quality is MetricQuality.INVALID

    @property
    def is_unknown(self) -> bool:
        return self.quality is MetricQuality.UNKNOWN

    @staticmethod
    def _normalize_required_string(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"MetricSample.{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"MetricSample.{field_name} must not be empty"
            )

        return normalized

    def __str__(self) -> str:
        return f"{self.metric}={self.value} {self.unit}"


@dataclass(frozen=True, slots=True)
class NodeMetric:
    """Collection of operational metric samples."""

    samples: tuple[MetricSample, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.samples, tuple):
            raise TypeError(
                "NodeMetric.samples must be a tuple"
            )

        seen: set[str] = set()

        for sample in self.samples:
            if not isinstance(sample, MetricSample):
                raise TypeError(
                    "NodeMetric entries must be MetricSample objects"
                )

            canonical_name = sample.metric.casefold()

            if canonical_name in seen:
                raise ValueError(
                    f"Duplicate metric sample: {sample.metric}"
                )

            seen.add(canonical_name)

    def get(
        self,
        metric: str,
    ) -> MetricSample | None:
        """Return a metric sample by canonical name."""
        normalized = self._normalize_metric_name(metric)

        for sample in self.samples:
            if sample.metric.casefold() == normalized.casefold():
                return sample

        return None

    def has_metric(
        self,
        metric: str,
    ) -> bool:
        """Return whether the collection contains a metric."""
        return self.get(metric) is not None

    @property
    def valid_samples(self) -> tuple[MetricSample, ...]:
        """Return samples that are not INVALID."""
        return tuple(
            sample
            for sample in self.samples
            if sample.quality is not MetricQuality.INVALID
        )

    @property
    def invalid_samples(self) -> tuple[MetricSample, ...]:
        """Return INVALID samples."""
        return tuple(
            sample
            for sample in self.samples
            if sample.quality is MetricQuality.INVALID
        )

    def __len__(self) -> int:
        return len(self.samples)

    def __contains__(self, metric: object) -> bool:
        if not isinstance(metric, str):
            return False

        return self.has_metric(metric)

    @staticmethod
    def _normalize_metric_name(metric: str) -> str:
        if not isinstance(metric, str):
            raise TypeError(
                "metric name must be a string"
            )

        normalized = metric.strip()

        if not normalized:
            raise ValueError(
                "metric name must not be empty"
            )

        return normalized
