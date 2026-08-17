"""Tests for HealthEvaluator."""

from datetime import datetime, timezone

import pytest

from app.noc.domain.node_health import NodeHealthState
from app.noc.domain.node_metric import (
    MetricQuality,
    MetricSample,
    NodeMetric,
)
from app.noc.services.health_evaluator import (
    HealthEvaluator,
    HealthThreshold,
)


NOW = datetime(
    2026,
    8,
    17,
    23,
    0,
    tzinfo=timezone.utc,
)


def sample(
    metric: str,
    value: float,
    quality: MetricQuality = MetricQuality.GOOD,
) -> MetricSample:
    return MetricSample(
        metric=metric,
        value=value,
        unit="percent",
        timestamp=NOW,
        quality=quality,
    )


def metrics(*samples: MetricSample) -> NodeMetric:
    return NodeMetric(samples=tuple(samples))


def test_empty_metrics_are_unknown() -> None:
    health = HealthEvaluator().evaluate(
        NodeMetric()
    )

    assert health.state is NodeHealthState.UNKNOWN


def test_healthy_metrics_are_healthy() -> None:
    health = HealthEvaluator().evaluate(
        metrics(
            sample("system.cpu.usage_percent", 25.0),
            sample("system.memory.usage_percent", 40.0),
            sample("system.disk.usage_percent", 50.0),
        )
    )

    assert health.state is NodeHealthState.HEALTHY


def test_cpu_warning() -> None:
    health = HealthEvaluator().evaluate(
        metrics(
            sample("system.cpu.usage_percent", 70.0)
        )
    )

    assert health.state is NodeHealthState.WARNING


def test_cpu_degraded() -> None:
    health = HealthEvaluator().evaluate(
        metrics(
            sample("system.cpu.usage_percent", 85.0)
        )
    )

    assert health.state is NodeHealthState.DEGRADED


def test_cpu_critical() -> None:
    health = HealthEvaluator().evaluate(
        metrics(
            sample("system.cpu.usage_percent", 95.0)
        )
    )

    assert health.state is NodeHealthState.CRITICAL


def test_worst_metric_determines_health() -> None:
    health = HealthEvaluator().evaluate(
        metrics(
            sample("system.cpu.usage_percent", 20.0),
            sample("system.memory.usage_percent", 72.0),
            sample("system.disk.usage_percent", 92.0),
        )
    )

    assert health.state is NodeHealthState.DEGRADED


def test_invalid_metric_is_ignored() -> None:
    health = HealthEvaluator().evaluate(
        metrics(
            sample(
                "system.cpu.usage_percent",
                99.0,
                MetricQuality.INVALID,
            )
        )
    )

    assert health.state is NodeHealthState.UNKNOWN


def test_unknown_metric_is_ignored() -> None:
    health = HealthEvaluator().evaluate(
        metrics(
            sample(
                "system.cpu.usage_percent",
                99.0,
                MetricQuality.UNKNOWN,
            )
        )
    )

    assert health.state is NodeHealthState.UNKNOWN


def test_unrelated_metrics_do_not_affect_health() -> None:
    health = HealthEvaluator().evaluate(
        metrics(
            sample("system.network.tx_bps", 5_000_000.0)
        )
    )

    assert health.state is NodeHealthState.UNKNOWN


def test_custom_threshold_policy() -> None:
    evaluator = HealthEvaluator(
        thresholds=(
            HealthThreshold(
                metric="custom.load",
                warning=50.0,
                degraded=70.0,
                critical=90.0,
            ),
        )
    )

    health = evaluator.evaluate(
        metrics(
            sample("custom.load", 75.0)
        )
    )

    assert health.state is NodeHealthState.DEGRADED


def test_threshold_rejects_invalid_order() -> None:
    with pytest.raises(ValueError):
        HealthThreshold(
            metric="system.cpu.usage_percent",
            warning=90.0,
            degraded=80.0,
            critical=95.0,
        )


def test_evaluator_requires_node_metric() -> None:
    with pytest.raises(TypeError):
        HealthEvaluator().evaluate(
            object()  # type: ignore[arg-type]
        )
