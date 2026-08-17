"""Tests for SystemCapacityProvider."""

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
from app.noc.domain.node_capacity import NodeCapacity
from app.noc.infrastructure.system_capacity_provider import (
    SystemCapacityProvider,
)


CAPTURED_AT = datetime(
    2026,
    8,
    17,
    22,
    30,
    tzinfo=timezone.utc,
)


def make_resources() -> SystemResources:
    return SystemResources(
        cpu=CPUInfo(
            usage_percent=25.0,
            logical_cores=8,
            physical_cores=4,
            frequency_mhz=2800.0,
            per_core_usage_percent=(
                20.0,
                21.0,
                22.0,
                23.0,
                24.0,
                25.0,
                26.0,
                27.0,
            ),
        ),
        memory=MemoryInfo(
            total_bytes=8_000_000_000,
            available_bytes=4_500_000_000,
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
            bytes_sent=1_000,
            bytes_received=2_000,
            packets_sent=10,
            packets_received=20,
            errors_in=0,
            errors_out=0,
            dropped_in=0,
            dropped_out=0,
        ),
        uptime=UptimeInfo(
            uptime_seconds=3600,
        ),
        captured_at=CAPTURED_AT,
    )


def test_provider_requires_system_resources() -> None:
    with pytest.raises(TypeError):
        SystemCapacityProvider().collect(
            object()  # type: ignore[arg-type]
        )


def test_provider_returns_node_capacity() -> None:
    capacity = SystemCapacityProvider().collect(
        make_resources()
    )

    assert isinstance(
        capacity,
        NodeCapacity,
    )

    assert len(capacity) == 2


def test_provider_maps_system_memory() -> None:
    capacity = SystemCapacityProvider().collect(
        make_resources()
    )

    memory = capacity.get(
        "System Memory"
    )

    assert memory is not None
    assert memory.maximum == 8_000_000_000
    assert memory.allocated == 3_000_000_000
    assert memory.reserved == 0
    assert memory.available == 5_000_000_000
    assert memory.unit == "bytes"


def test_provider_maps_system_storage() -> None:
    capacity = SystemCapacityProvider().collect(
        make_resources()
    )

    storage = capacity.get(
        "System Storage"
    )

    assert storage is not None
    assert storage.maximum == 500_000_000_000
    assert storage.allocated == 125_000_000_000
    assert storage.reserved == 0
    assert storage.available == 375_000_000_000
    assert storage.unit == "bytes"


def test_memory_capacity_utilization_is_available() -> None:
    capacity = SystemCapacityProvider().collect(
        make_resources()
    )

    memory = capacity.get(
        "System Memory"
    )

    assert memory is not None

    assert memory.utilization_percent == pytest.approx(
        37.5
    )


def test_storage_capacity_utilization_is_available() -> None:
    capacity = SystemCapacityProvider().collect(
        make_resources()
    )

    storage = capacity.get(
        "System Storage"
    )

    assert storage is not None

    assert storage.utilization_percent == pytest.approx(
        25.0
    )
