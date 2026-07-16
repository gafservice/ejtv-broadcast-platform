"""Pruebas de los objetos de dominio de recursos del sistema."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    SystemResources,
    UptimeInfo,
)


def build_system_resources() -> SystemResources:
    """Construye una medición válida para las pruebas."""

    return SystemResources(
        cpu=CPUInfo(
            usage_percent=25.5,
            logical_cores=8,
            physical_cores=4,
            frequency_mhz=2800.0,
        ),
        memory=MemoryInfo(
            total_bytes=8_000,
            available_bytes=5_000,
            used_bytes=3_000,
            usage_percent=37.5,
        ),
        disk=DiskInfo(
            total_bytes=100_000,
            used_bytes=40_000,
            free_bytes=60_000,
            usage_percent=40.0,
        ),
        uptime=UptimeInfo(
            uptime_seconds=86_400,
        ),
        captured_at=datetime.now(UTC),
    )


def test_cpu_info_creation() -> None:
    cpu = CPUInfo(
        usage_percent=12,
        logical_cores=8,
        physical_cores=4,
        frequency_mhz=2800,
    )

    assert cpu.usage_percent == 12.0
    assert cpu.logical_cores == 8
    assert cpu.physical_cores == 4
    assert cpu.frequency_mhz == 2800.0


def test_cpu_info_accepts_unavailable_optional_values() -> None:
    cpu = CPUInfo(
        usage_percent=10.0,
        logical_cores=8,
        physical_cores=None,
        frequency_mhz=None,
    )

    assert cpu.physical_cores is None
    assert cpu.frequency_mhz is None


@pytest.mark.parametrize(
    "usage_percent",
    [-1, 100.1],
)
def test_cpu_info_rejects_invalid_percentage(
    usage_percent: float,
) -> None:
    with pytest.raises(ValueError):
        CPUInfo(
            usage_percent=usage_percent,
            logical_cores=8,
            physical_cores=4,
            frequency_mhz=2800,
        )


def test_memory_info_creation() -> None:
    memory = MemoryInfo(
        total_bytes=8_000,
        available_bytes=5_000,
        used_bytes=3_000,
        usage_percent=37.5,
    )

    assert memory.total_bytes == 8_000
    assert memory.available_bytes == 5_000
    assert memory.used_bytes == 3_000
    assert memory.usage_percent == 37.5


def test_memory_rejects_used_value_above_total() -> None:
    with pytest.raises(ValueError):
        MemoryInfo(
            total_bytes=8_000,
            available_bytes=1_000,
            used_bytes=9_000,
            usage_percent=90.0,
        )


def test_disk_info_creation() -> None:
    disk = DiskInfo(
        total_bytes=100_000,
        used_bytes=40_000,
        free_bytes=60_000,
        usage_percent=40.0,
    )

    assert disk.total_bytes == 100_000
    assert disk.used_bytes == 40_000
    assert disk.free_bytes == 60_000
    assert disk.usage_percent == 40.0


def test_uptime_rejects_negative_value() -> None:
    with pytest.raises(ValueError):
        UptimeInfo(uptime_seconds=-1)


def test_system_resources_creation() -> None:
    resources = build_system_resources()

    assert isinstance(resources.cpu, CPUInfo)
    assert isinstance(resources.memory, MemoryInfo)
    assert isinstance(resources.disk, DiskInfo)
    assert isinstance(resources.uptime, UptimeInfo)
    assert resources.captured_at.tzinfo is not None


def test_system_resources_requires_timezone() -> None:
    with pytest.raises(ValueError):
        SystemResources(
            cpu=CPUInfo(
                usage_percent=10.0,
                logical_cores=8,
                physical_cores=4,
                frequency_mhz=2800.0,
            ),
            memory=MemoryInfo(
                total_bytes=8_000,
                available_bytes=5_000,
                used_bytes=3_000,
                usage_percent=37.5,
            ),
            disk=DiskInfo(
                total_bytes=100_000,
                used_bytes=40_000,
                free_bytes=60_000,
                usage_percent=40.0,
            ),
            uptime=UptimeInfo(
                uptime_seconds=86_400,
            ),
            captured_at=datetime.now(),
        )


def test_system_resources_is_immutable() -> None:
    resources = build_system_resources()

    with pytest.raises(FrozenInstanceError):
        resources.cpu = CPUInfo(  # type: ignore[misc]
            usage_percent=50.0,
            logical_cores=8,
            physical_cores=4,
            frequency_mhz=2800.0,
        )