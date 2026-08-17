"""Health evaluation policy for the NOC.

ENG-013B — Node SDK
NCS reference: 12-NODE-HEALTH.md

HealthEvaluator derives the integral NodeHealth of an instance from
its current canonical operational metrics.

The evaluator is intentionally independent from Linux, adapters,
runtime refresh and API layers.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_metric import (
    MetricQuality,
    MetricSample,
    NodeMetric,
)


@dataclass(frozen=True, slots=True)
class HealthThreshold:
    """Threshold policy for one percentage-based metric."""

    metric: str
    warning: float
    degraded: float
    critical: float

    def __post_init__(self) -> None:
        if not isinstance(self.metric, str):
            raise TypeError("metric must be a string")

        if not self.metric.strip():
            raise ValueError("metric must not be empty")

        if not (
            0.0
            <= self.warning
            <= self.degraded
            <= self.critical
            <= 100.0
        ):
            raise ValueError(
                "thresholds must satisfy "
                "0 <= warning <= degraded <= critical <= 100"
            )


DEFAULT_THRESHOLDS = (
    HealthThreshold(
        metric="system.cpu.usage_percent",
        warning=70.0,
        degraded=85.0,
        critical=95.0,
    ),
    HealthThreshold(
        metric="system.memory.usage_percent",
        warning=70.0,
        degraded=85.0,
        critical=95.0,
    ),
    HealthThreshold(
        metric="system.disk.usage_percent",
        warning=75.0,
        degraded=90.0,
        critical=97.0,
    ),
)


class HealthEvaluator:
    """Evaluate integral NodeHealth from current NodeMetric state."""

    def __init__(
        self,
        thresholds: tuple[HealthThreshold, ...] = DEFAULT_THRESHOLDS,
    ) -> None:
        if not isinstance(thresholds, tuple):
            raise TypeError("thresholds must be a tuple")

        for threshold in thresholds:
            if not isinstance(threshold, HealthThreshold):
                raise TypeError(
                    "thresholds must contain HealthThreshold objects"
                )

        self._thresholds = thresholds

    @property
    def thresholds(self) -> tuple[HealthThreshold, ...]:
        return self._thresholds

    def evaluate(
        self,
        metrics: NodeMetric,
    ) -> NodeHealth:
        """Return integral health for the supplied current metrics."""

        if not isinstance(metrics, NodeMetric):
            raise TypeError("metrics must be a NodeMetric")

        states: list[NodeHealthState] = []

        for threshold in self._thresholds:
            sample = metrics.get(threshold.metric)

            if sample is None:
                continue

            state = self._evaluate_sample(
                sample,
                threshold,
            )

            if state is None:
                continue

            states.append(state)

        if not states:
            return NodeHealth(
                NodeHealthState.UNKNOWN
            )

        worst = max(
            states,
            key=lambda state: {
                NodeHealthState.HEALTHY: 0,
                NodeHealthState.WARNING: 1,
                NodeHealthState.DEGRADED: 2,
                NodeHealthState.CRITICAL: 3,
            }[state],
        )

        return NodeHealth(worst)

    @staticmethod
    def _evaluate_sample(
        sample: MetricSample,
        threshold: HealthThreshold,
    ) -> NodeHealthState | None:
        if sample.quality in {
            MetricQuality.INVALID,
            MetricQuality.UNKNOWN,
        }:
            return None

        value = float(sample.value)

        if value >= threshold.critical:
            return NodeHealthState.CRITICAL

        if value >= threshold.degraded:
            return NodeHealthState.DEGRADED

        if value >= threshold.warning:
            return NodeHealthState.WARNING

        return NodeHealthState.HEALTHY
