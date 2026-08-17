"""Tests for NetworkRateMetricsProvider."""

from datetime import datetime, timezone

import pytest

from app.domain.system import NetworkRate
from app.noc.domain.node_metric import (
    MetricQuality,
    MetricSample,
)
from app.noc.infrastructure.network_rate_metrics_provider import (
    NetworkRateMetricsProvider,
)


CAPTURED_AT = datetime(
    2026,
    8,
    15,
    23,
    30,
    tzinfo=timezone.utc,
)


def make_rate(
    *,
    rx_bps=4_000_000.0,
    tx_bps=2_000_000.0,
) -> NetworkRate:
    return NetworkRate(
        interface="ens2f0",
        rx_bps=rx_bps,
        tx_bps=tx_bps,
        interval_seconds=5.0,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
        captured_at=CAPTURED_AT,
    )


def samples_by_name(
    samples: tuple[MetricSample, ...],
) -> dict[str, MetricSample]:
    return {
        sample.metric: sample
        for sample in samples
    }


def test_provider_requires_network_rate() -> None:
    provider = NetworkRateMetricsProvider()

    with pytest.raises(TypeError):
        provider.collect(
            object()  # type: ignore[arg-type]
        )


def test_unavailable_rates_produce_no_metrics() -> None:
    provider = NetworkRateMetricsProvider()

    rate = make_rate(
        rx_bps=None,
        tx_bps=None,
    )

    assert provider.collect(rate) == ()


def test_provider_generates_two_rate_metrics() -> None:
    provider = NetworkRateMetricsProvider()

    samples = provider.collect(
        make_rate()
    )

    assert len(samples) == 2

    assert all(
        isinstance(sample, MetricSample)
        for sample in samples
    )


def test_provider_maps_rx_bps() -> None:
    provider = NetworkRateMetricsProvider()

    samples = samples_by_name(
        provider.collect(
            make_rate()
        )
    )

    sample = samples[
        "system.network.rx_bps"
    ]

    assert sample.value == 4_000_000.0
    assert sample.unit == "bps"


def test_provider_maps_tx_bps() -> None:
    provider = NetworkRateMetricsProvider()

    samples = samples_by_name(
        provider.collect(
            make_rate()
        )
    )

    sample = samples[
        "system.network.tx_bps"
    ]

    assert sample.value == 2_000_000.0
    assert sample.unit == "bps"


def test_provider_uses_rate_timestamp() -> None:
    provider = NetworkRateMetricsProvider()

    samples = provider.collect(
        make_rate()
    )

    assert {
        sample.timestamp
        for sample in samples
    } == {
        CAPTURED_AT
    }


def test_provider_marks_rate_metrics_good() -> None:
    provider = NetworkRateMetricsProvider()

    samples = provider.collect(
        make_rate()
    )

    assert all(
        sample.quality
        is MetricQuality.GOOD
        for sample in samples
    )


def test_provider_generates_quality_rate_metrics() -> None:
    provider = NetworkRateMetricsProvider()

    rate = NetworkRate(
        interface="ens2f0",
        rx_bps=4_000_000.0,
        tx_bps=2_000_000.0,
        interval_seconds=5.0,
        errors_in=10,
        errors_out=20,
        dropped_in=30,
        dropped_out=40,
        captured_at=CAPTURED_AT,
        errors_in_per_second=1.0,
        errors_out_per_second=2.0,
        dropped_in_per_second=3.0,
        dropped_out_per_second=4.0,
    )

    samples = samples_by_name(
        provider.collect(rate)
    )

    assert samples[
        "system.network.errors_in_per_second"
    ].value == 1.0

    assert samples[
        "system.network.errors_out_per_second"
    ].value == 2.0

    assert samples[
        "system.network.dropped_in_per_second"
    ].value == 3.0

    assert samples[
        "system.network.dropped_out_per_second"
    ].value == 4.0


def test_provider_uses_count_per_second_units() -> None:
    provider = NetworkRateMetricsProvider()

    rate = NetworkRate(
        interface="ens2f0",
        rx_bps=4_000_000.0,
        tx_bps=2_000_000.0,
        interval_seconds=5.0,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
        captured_at=CAPTURED_AT,
        errors_in_per_second=0.0,
        errors_out_per_second=0.0,
        dropped_in_per_second=0.0,
        dropped_out_per_second=0.0,
    )

    samples = samples_by_name(
        provider.collect(rate)
    )

    for name in {
        "system.network.errors_in_per_second",
        "system.network.errors_out_per_second",
        "system.network.dropped_in_per_second",
        "system.network.dropped_out_per_second",
    }:
        assert samples[name].unit == "count/s"


def test_unavailable_quality_rates_are_omitted() -> None:
    provider = NetworkRateMetricsProvider()

    rate = make_rate()

    samples = provider.collect(rate)

    assert {
        sample.metric
        for sample in samples
    } == {
        "system.network.rx_bps",
        "system.network.tx_bps",
    }
