"""Tests for SystemMetricsProvider."""

from datetime import datetime, timezone

import pytest

from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    NetworkInfo,
    SystemResources,
    UptimeInfo,
)
from app.noc.domain.node_metric import (
    MetricQuality,
    MetricSample,
)
from app.noc.infrastructure.system_metrics_provider import (
    SystemMetricsProvider,
)


CAPTURED_AT = datetime(
    2026,
    8,
    15,
    22,
    30,
    tzinfo=timezone.utc,
)


def make_resources() -> SystemResources:
    return SystemResources(
        cpu=CPUInfo(
            usage_percent=42.5,
            logical_cores=8,
            physical_cores=4,
            frequency_mhz=2800.0,
            per_core_usage_percent=(
                40.0,
                41.0,
                42.0,
                43.0,
                44.0,
                45.0,
                46.0,
                47.0,
            ),
        ),
        memory=MemoryInfo(
            total_bytes=8_000_000_000,
            available_bytes=5_000_000_000,
            used_bytes=3_000_000_000,
            usage_percent=37.5,
            free_bytes=1_000_000_000,
            cached_bytes=1_500_000_000,
            buffers_bytes=500_000_000,
        ),
        disk=DiskInfo(
            total_bytes=500_000_000_000,
            used_bytes=125_000_000_000,
            free_bytes=375_000_000_000,
            usage_percent=25.0,
            device="/dev/sda2",
            mount_point="/",
            filesystem_type="ext4",
        ),
        network=NetworkInfo(
            interface="ens2f0",
            bytes_sent=18_000_000,
            bytes_received=25_000_000,
            packets_sent=20_000,
            packets_received=30_000,
            errors_in=0,
            errors_out=0,
            dropped_in=0,
            dropped_out=0,
        ),
        uptime=UptimeInfo(
            uptime_seconds=3_600,
        ),
        captured_at=CAPTURED_AT,
    )


def samples_by_name(
    samples: tuple[MetricSample, ...],
) -> dict[str, MetricSample]:
    return {
        sample.metric: sample
        for sample in samples
    }


def test_provider_requires_system_resources() -> None:
    provider = SystemMetricsProvider()

    with pytest.raises(TypeError):
        provider.collect(
            object()  # type: ignore[arg-type]
        )


def test_provider_generates_six_metrics() -> None:
    provider = SystemMetricsProvider()

    samples = provider.collect(
        make_resources()
    )

    assert len(samples) == 6

    assert all(
        isinstance(sample, MetricSample)
        for sample in samples
    )


def test_provider_uses_common_capture_timestamp() -> None:
    provider = SystemMetricsProvider()

    samples = provider.collect(
        make_resources()
    )

    assert {
        sample.timestamp
        for sample in samples
    } == {
        CAPTURED_AT
    }


def test_provider_maps_cpu_usage() -> None:
    provider = SystemMetricsProvider()

    samples = samples_by_name(
        provider.collect(make_resources())
    )

    sample = samples[
        "system.cpu.usage_percent"
    ]

    assert sample.value == 42.5
    assert sample.unit == "%"


def test_provider_maps_memory_usage() -> None:
    provider = SystemMetricsProvider()

    samples = samples_by_name(
        provider.collect(make_resources())
    )

    sample = samples[
        "system.memory.usage_percent"
    ]

    assert sample.value == 37.5
    assert sample.unit == "%"


def test_provider_maps_disk_usage() -> None:
    provider = SystemMetricsProvider()

    samples = samples_by_name(
        provider.collect(make_resources())
    )

    sample = samples[
        "system.disk.usage_percent"
    ]

    assert sample.value == 25.0
    assert sample.unit == "%"


def test_provider_maps_network_receive_counter() -> None:
    provider = SystemMetricsProvider()

    samples = samples_by_name(
        provider.collect(make_resources())
    )

    sample = samples[
        "system.network.rx_bytes"
    ]

    assert sample.value == 25_000_000
    assert sample.unit == "bytes"


def test_provider_maps_network_transmit_counter() -> None:
    provider = SystemMetricsProvider()

    samples = samples_by_name(
        provider.collect(make_resources())
    )

    sample = samples[
        "system.network.tx_bytes"
    ]

    assert sample.value == 18_000_000
    assert sample.unit == "bytes"


def test_provider_maps_uptime() -> None:
    provider = SystemMetricsProvider()

    samples = samples_by_name(
        provider.collect(make_resources())
    )

    sample = samples[
        "system.uptime_seconds"
    ]

    assert sample.value == 3_600
    assert sample.unit == "s"


def test_provider_marks_all_samples_good() -> None:
    provider = SystemMetricsProvider()

    samples = provider.collect(
        make_resources()
    )

    assert all(
        sample.quality
        is MetricQuality.GOOD
        for sample in samples
    )


def test_provider_uses_canonical_metric_names() -> None:
    provider = SystemMetricsProvider()

    samples = provider.collect(
        make_resources()
    )

    assert {
        sample.metric
        for sample in samples
    } == {
        "system.cpu.usage_percent",
        "system.memory.usage_percent",
        "system.disk.usage_percent",
        "system.network.rx_bytes",
        "system.network.tx_bytes",
        "system.uptime_seconds",
    }
