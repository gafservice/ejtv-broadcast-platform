"""Tests for NodeMetric.

ENG-013B — Node SDK
NCS reference: 16-NODE-METRIC.md
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node_metric import (
    MetricQuality,
    MetricSample,
    NodeMetric,
)


def make_sample(
    metric: str = "cpu_usage",
    value: float = 82.3,
    unit: str = "%",
    quality: MetricQuality = MetricQuality.GOOD,
) -> MetricSample:
    return MetricSample(
        metric=metric,
        value=value,
        unit=unit,
        timestamp=datetime.now(timezone.utc),
        quality=quality,
    )


def test_metric_quality_contains_canonical_values() -> None:
    expected = {
        "GOOD",
        "DEGRADED",
        "INVALID",
        "UNKNOWN",
    }

    assert {
        quality.value for quality in MetricQuality
    } == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("good", MetricQuality.GOOD),
        (" DEGRADED ", MetricQuality.DEGRADED),
        ("invalid", MetricQuality.INVALID),
        ("unknown", MetricQuality.UNKNOWN),
    ],
)
def test_metric_quality_from_value(
    raw: str,
    expected: MetricQuality,
) -> None:
    assert MetricQuality.from_value(raw) is expected


def test_metric_quality_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        MetricQuality.from_value("BAD")


def test_metric_quality_rejects_empty_value() -> None:
    with pytest.raises(ValueError):
        MetricQuality.from_value("   ")


def test_metric_sample_can_be_created() -> None:
    sample = make_sample()

    assert sample.metric == "cpu_usage"
    assert sample.value == 82.3
    assert sample.unit == "%"
    assert sample.quality is MetricQuality.GOOD


def test_metric_sample_normalizes_strings() -> None:
    sample = MetricSample(
        metric="  cpu_usage  ",
        value=80,
        unit="  %  ",
        timestamp=datetime.now(timezone.utc),
    )

    assert sample.metric == "cpu_usage"
    assert sample.unit == "%"


@pytest.mark.parametrize(
    "field",
    ["metric", "unit"],
)
def test_metric_sample_rejects_empty_strings(
    field: str,
) -> None:
    values = {
        "metric": "cpu_usage",
        "value": 80.0,
        "unit": "%",
        "timestamp": datetime.now(timezone.utc),
        "quality": MetricQuality.GOOD,
    }

    values[field] = "   "

    with pytest.raises(ValueError):
        MetricSample(**values)


@pytest.mark.parametrize(
    "value",
    [
        float("inf"),
        float("-inf"),
        float("nan"),
    ],
)
def test_metric_sample_rejects_non_finite_values(
    value: float,
) -> None:
    with pytest.raises(ValueError):
        make_sample(value=value)


def test_metric_sample_rejects_boolean_value() -> None:
    with pytest.raises(TypeError):
        MetricSample(
            metric="cpu_usage",
            value=True,
            unit="%",
            timestamp=datetime.now(timezone.utc),
        )


def test_metric_sample_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError):
        MetricSample(
            metric="cpu_usage",
            value=80,
            unit="%",
            timestamp=datetime(2026, 8, 11, 18, 0),
        )


def test_metric_sample_rejects_non_utc_timestamp() -> None:
    non_utc = timezone(timedelta(hours=-6))

    with pytest.raises(ValueError):
        MetricSample(
            metric="cpu_usage",
            value=80,
            unit="%",
            timestamp=datetime(
                2026,
                8,
                11,
                12,
                0,
                tzinfo=non_utc,
            ),
        )


def test_metric_sample_quality_flags() -> None:
    assert make_sample(
        quality=MetricQuality.GOOD
    ).is_good is True

    assert make_sample(
        quality=MetricQuality.DEGRADED
    ).is_degraded is True

    assert make_sample(
        quality=MetricQuality.INVALID
    ).is_invalid is True

    assert make_sample(
        quality=MetricQuality.UNKNOWN
    ).is_unknown is True


def test_metric_sample_is_immutable() -> None:
    sample = make_sample()

    with pytest.raises(AttributeError):
        sample.value = 90  # type: ignore[misc]


def test_metric_sample_string_representation() -> None:
    sample = make_sample()

    assert str(sample) == "cpu_usage=82.3 %"


def test_node_metric_can_be_empty() -> None:
    metrics = NodeMetric()

    assert metrics.samples == ()
    assert len(metrics) == 0


def test_node_metric_accepts_multiple_samples() -> None:
    metrics = NodeMetric(
        samples=(
            make_sample("cpu_usage", 82.3, "%"),
            make_sample("memory_usage", 61.2, "%"),
        )
    )

    assert len(metrics) == 2


def test_node_metric_rejects_duplicate_metric_names() -> None:
    with pytest.raises(ValueError):
        NodeMetric(
            samples=(
                make_sample("cpu_usage", 80, "%"),
                make_sample("CPU_USAGE", 90, "%"),
            )
        )


def test_node_metric_get_metric() -> None:
    sample = make_sample()

    metrics = NodeMetric(
        samples=(sample,)
    )

    assert metrics.get("CPU_USAGE") is sample


def test_node_metric_get_unknown_returns_none() -> None:
    metrics = NodeMetric()

    assert metrics.get("cpu_usage") is None


def test_node_metric_has_metric() -> None:
    metrics = NodeMetric(
        samples=(make_sample(),)
    )

    assert metrics.has_metric("cpu_usage") is True
    assert metrics.has_metric("packet_loss") is False


def test_node_metric_valid_samples_exclude_invalid() -> None:
    metrics = NodeMetric(
        samples=(
            make_sample(
                "cpu_usage",
                80,
                "%",
                MetricQuality.GOOD,
            ),
            make_sample(
                "temperature",
                0,
                "C",
                MetricQuality.INVALID,
            ),
        )
    )

    assert len(metrics.valid_samples) == 1
    assert metrics.valid_samples[0].metric == "cpu_usage"


def test_node_metric_invalid_samples() -> None:
    metrics = NodeMetric(
        samples=(
            make_sample(
                "cpu_usage",
                80,
                "%",
                MetricQuality.GOOD,
            ),
            make_sample(
                "temperature",
                0,
                "C",
                MetricQuality.INVALID,
            ),
        )
    )

    assert len(metrics.invalid_samples) == 1
    assert metrics.invalid_samples[0].metric == "temperature"


def test_node_metric_contains_metric() -> None:
    metrics = NodeMetric(
        samples=(make_sample(),)
    )

    assert "cpu_usage" in metrics
    assert "CPU_USAGE" in metrics
    assert "packet_loss" not in metrics


def test_node_metric_rejects_non_tuple_samples() -> None:
    with pytest.raises(TypeError):
        NodeMetric(
            samples=[]  # type: ignore[arg-type]
        )


def test_node_metric_rejects_invalid_entry() -> None:
    with pytest.raises(TypeError):
        NodeMetric(
            samples=(
                "cpu_usage",  # type: ignore[arg-type]
            )
        )
