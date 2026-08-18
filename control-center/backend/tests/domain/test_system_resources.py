"""Pruebas de los objetos de dominio de recursos del sistema."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    NetworkInfo,
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
             free_bytes=2_000,
             cached_bytes=800,
       	     buffers_bytes=200,
        ),
       
        disk=DiskInfo(
            total_bytes=100_000,
            used_bytes=40_000,
            free_bytes=60_000,
            usage_percent=40.0,
        ),

        network=NetworkInfo(
            interface="ens2f0",
            bytes_sent=1_000_000,
            bytes_received=2_000_000,
            packets_sent=10_000,
            packets_received=20_000,
            errors_in=0,
            errors_out=0,
            dropped_in=0,
            dropped_out=0,
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
    assert isinstance(resources.network, NetworkInfo)
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
            network=NetworkInfo(
                interface="ens2f0",
                bytes_sent=1_000_000,
                bytes_received=2_000_000,
                packets_sent=10_000,
                packets_received=20_000,
                errors_in=0,
                errors_out=0,
                dropped_in=0,
                dropped_out=0,
            ),

            uptime=UptimeInfo(
                uptime_seconds=86_400,
            ),
            captured_at=datetime.now(),
        )


def test_system_resources_is_immutable() -> None:
    resources = build_system_resources()

    with pytest.raises(FrozenInstanceError):
        resources.cpu = resources.cpu

def test_cpu_info_accepts_usage_per_logical_core() -> None:
    cpu = CPUInfo(
        usage_percent=31.25,
        logical_cores=4,
        physical_cores=2,
        frequency_mhz=2800.0,
        per_core_usage_percent=(
            10,
            25.5,
            40,
            49.5,
        ),
    )

    assert cpu.per_core_usage_percent == (
        10.0,
        25.5,
        40.0,
        49.5,
    )
    assert cpu.minimum_core_usage_percent == 10.0
    assert cpu.maximum_core_usage_percent == 49.5


@pytest.mark.parametrize(
    "per_core_usage_percent",
    [
        (-1.0, 20.0),
        (20.0, 100.1),
        (True, 20.0),
        ("20", 30.0),
    ],
)
def test_cpu_info_rejects_invalid_core_percentage(
    per_core_usage_percent: tuple[object, ...],
) -> None:
    with pytest.raises(ValueError):
        CPUInfo(
            usage_percent=25.0,
            logical_cores=2,
            physical_cores=1,
            frequency_mhz=2800.0,
            per_core_usage_percent=per_core_usage_percent,
        )


def test_cpu_info_rejects_core_count_mismatch() -> None:
    with pytest.raises(ValueError):
        CPUInfo(
            usage_percent=25.0,
            logical_cores=4,
            physical_cores=2,
            frequency_mhz=2800.0,
            per_core_usage_percent=(
                10.0,
                20.0,
            ),
        )


def test_cpu_info_accepts_unavailable_core_measurements() -> None:
    cpu = CPUInfo(
        usage_percent=25.0,
        logical_cores=4,
        physical_cores=2,
        frequency_mhz=2800.0,
    )

    assert cpu.per_core_usage_percent == ()
    assert cpu.minimum_core_usage_percent is None
    assert cpu.maximum_core_usage_percent is None

def test_disk_info_accepts_storage_identity() -> None:
    disk = DiskInfo(
        total_bytes=100_000,
        used_bytes=40_000,
        free_bytes=60_000,
        usage_percent=40.0,
        device="/dev/sda2",
        mount_point="/",
        filesystem_type="ext4",
    )

    assert disk.device == "/dev/sda2"
    assert disk.mount_point == "/"
    assert disk.filesystem_type == "ext4"

def test_memory_info_accepts_extended_memory_metrics() -> None:
    memory = MemoryInfo(
        total_bytes=8_000,
        available_bytes=5_000,
        used_bytes=3_000,
        usage_percent=37.5,
        free_bytes=2_000,
        cached_bytes=800,
        buffers_bytes=200,
    )

    assert memory.free_bytes == 2_000
    assert memory.cached_bytes == 800
    assert memory.buffers_bytes == 200


@pytest.mark.parametrize(
    "field_name",
    [
        "free_bytes",
        "cached_bytes",
        "buffers_bytes",
    ],
)
def test_memory_info_rejects_negative_extended_metrics(
    field_name: str,
) -> None:
    values = {
        "total_bytes": 8_000,
        "available_bytes": 5_000,
        "used_bytes": 3_000,
        "usage_percent": 37.5,
        "free_bytes": 2_000,
        "cached_bytes": 800,
        "buffers_bytes": 200,
    }

    values[field_name] = -1

    with pytest.raises(ValueError):
        MemoryInfo(**values)

@pytest.mark.parametrize(
    "field_name",
    [
        "device",
        "mount_point",
        "filesystem_type",
    ],
)
def test_disk_info_rejects_empty_storage_identity(
    field_name: str,
) -> None:
    values = {
        "total_bytes": 100_000,
        "used_bytes": 40_000,
        "free_bytes": 60_000,
        "usage_percent": 40.0,
        "device": "/dev/sda2",
        "mount_point": "/",
        "filesystem_type": "ext4",
    }

    values[field_name] = "   "

    with pytest.raises(ValueError):
        DiskInfo(**values)

def test_network_info_creation() -> None:
    network = NetworkInfo(
        interface="ens2f0",
        bytes_sent=1_000_000,
        bytes_received=2_000_000,
        packets_sent=10_000,
        packets_received=20_000,
        errors_in=2,
        errors_out=1,
        dropped_in=4,
        dropped_out=3,
    )

    assert network.interface == "ens2f0"
    assert network.bytes_sent == 1_000_000
    assert network.bytes_received == 2_000_000
    assert network.packets_sent == 10_000
    assert network.packets_received == 20_000
    assert network.errors_in == 2
    assert network.errors_out == 1
    assert network.dropped_in == 4
    assert network.dropped_out == 3


@pytest.mark.parametrize(
    "field_name",
    [
        "bytes_sent",
        "bytes_received",
        "packets_sent",
        "packets_received",
        "errors_in",
        "errors_out",
        "dropped_in",
        "dropped_out",
    ],
)
def test_network_info_rejects_negative_counters(
    field_name: str,
) -> None:
    values = {
        "interface": "ens2f0",
        "bytes_sent": 1_000_000,
        "bytes_received": 2_000_000,
        "packets_sent": 10_000,
        "packets_received": 20_000,
        "errors_in": 2,
        "errors_out": 1,
        "dropped_in": 4,
        "dropped_out": 3,
    }

    values[field_name] = -1

    with pytest.raises(ValueError):
        NetworkInfo(**values)


@pytest.mark.parametrize(
    "interface",
    [
        "",
        "   ",
    ],
)
def test_network_info_rejects_empty_interface(
    interface: str,
) -> None:
    with pytest.raises(ValueError):
        NetworkInfo(
            interface=interface,
            bytes_sent=1_000_000,
            bytes_received=2_000_000,
            packets_sent=10_000,
            packets_received=20_000,
            errors_in=0,
            errors_out=0,
            dropped_in=0,
            dropped_out=0,
        )

def test_system_resources_legacy_network_populates_networks() -> None:
    resources = build_system_resources()

    assert resources.networks == (
        resources.network,
    )


def test_system_resources_accepts_multiple_network_interfaces() -> None:
    resources = build_system_resources()

    backup = NetworkInfo(
        interface="ens2f1",
        bytes_sent=500,
        bytes_received=1_000,
        packets_sent=5,
        packets_received=10,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )

    multi = SystemResources(
        cpu=resources.cpu,
        memory=resources.memory,
        disk=resources.disk,
        network=resources.network,
        uptime=resources.uptime,
        captured_at=resources.captured_at,
        networks=(
            resources.network,
            backup,
        ),
    )

    assert len(multi.networks) == 2

    assert tuple(
        item.interface
        for item in multi.networks
    ) == (
        "ens2f0",
        "ens2f1",
    )


def test_system_resources_rejects_duplicate_network_interfaces() -> None:
    resources = build_system_resources()

    with pytest.raises(ValueError):
        SystemResources(
            cpu=resources.cpu,
            memory=resources.memory,
            disk=resources.disk,
            network=resources.network,
            uptime=resources.uptime,
            captured_at=resources.captured_at,
            networks=(
                resources.network,
                resources.network,
            ),
        )


def test_system_resources_requires_primary_network_in_networks() -> None:
    resources = build_system_resources()

    other = NetworkInfo(
        interface="ens2f1",
        bytes_sent=500,
        bytes_received=1_000,
        packets_sent=5,
        packets_received=10,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )

    with pytest.raises(ValueError):
        SystemResources(
            cpu=resources.cpu,
            memory=resources.memory,
            disk=resources.disk,
            network=resources.network,
            uptime=resources.uptime,
            captured_at=resources.captured_at,
            networks=(other,),
        )


def test_system_resources_rejects_non_tuple_networks() -> None:
    resources = build_system_resources()

    with pytest.raises(ValueError):
        SystemResources(
            cpu=resources.cpu,
            memory=resources.memory,
            disk=resources.disk,
            network=resources.network,
            uptime=resources.uptime,
            captured_at=resources.captured_at,
            networks=[  # type: ignore[arg-type]
                resources.network,
            ],
        )
