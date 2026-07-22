"""Pruebas del contrato y del adaptador Linux."""

import inspect
import pytest
from unittest.mock import patch

from app.adapters.base.system_adapter import SystemAdapter
from app.adapters.linux.linux_system_adapter import LinuxSystemAdapter
from app.domain.system import (
    ServiceInstance,
    ServiceStatus,
)


def test_system_adapter_is_abstract() -> None:
    assert inspect.isabstract(SystemAdapter)


def test_linux_adapter_implements_system_contract() -> None:
    assert issubclass(LinuxSystemAdapter, SystemAdapter)


def test_linux_adapter_is_concrete() -> None:
    assert not inspect.isabstract(LinuxSystemAdapter)


def test_hostname() -> None:
    adapter = LinuxSystemAdapter()

    with patch(
        "app.adapters.linux.linux_system_adapter.socket.gethostname",
        return_value="ejtv-01",
    ):
        assert adapter.hostname() == "ejtv-01"


def test_operating_system_uses_pretty_name() -> None:
    adapter = LinuxSystemAdapter()

    with patch(
        "app.adapters.linux.linux_system_adapter."
        "platform.freedesktop_os_release",
        return_value={
            "NAME": "Ubuntu",
            "VERSION": "24.04.4 LTS",
            "PRETTY_NAME": "Ubuntu 24.04.4 LTS",
        },
    ):
        assert adapter.operating_system() == "Ubuntu 24.04.4 LTS"


def test_operating_system_fallback() -> None:
    adapter = LinuxSystemAdapter()

    with (
        patch(
            "app.adapters.linux.linux_system_adapter."
            "platform.freedesktop_os_release",
            side_effect=OSError,
        ),
        patch(
            "app.adapters.linux.linux_system_adapter.platform.platform",
            return_value="Linux-6.8.0-x86_64",
        ),
    ):
        assert adapter.operating_system() == "Linux-6.8.0-x86_64"


def test_kernel() -> None:
    adapter = LinuxSystemAdapter()

    with patch(
        "app.adapters.linux.linux_system_adapter.platform.release",
        return_value="6.8.0-71-generic",
    ):
        assert adapter.kernel() == "6.8.0-71-generic"

        
def test_cpu_info() -> None:
    adapter = LinuxSystemAdapter()

    with (
        patch(
            "app.adapters.linux.linux_system_adapter."
            "psutil.cpu_percent",
            side_effect=[
                25.5,
                [
                    10.0,
                    20.0,
                    30.0,
                    40.0,
                    15.0,
                    25.0,
                    35.0,
                    45.0,
                ],
            ],
        ),
        patch(
            "app.adapters.linux.linux_system_adapter."
            "psutil.cpu_count",
            side_effect=[8, 4],
        ),
        patch(
            "app.adapters.linux.linux_system_adapter."
            "psutil.cpu_freq",
            return_value=type(
                "CPUFrequency",
                (),
                {"current": 2800.0},
            )(),
        ),
    ):
        result = adapter.cpu_info()

    assert result.usage_percent == 25.5
    assert result.logical_cores == 8
    assert result.physical_cores == 4
    assert result.frequency_mhz == 2800.0
    assert result.per_core_usage_percent == (
        10.0,
        20.0,
        30.0,
        40.0,
        15.0,
        25.0,
        35.0,
        45.0,
    )
    assert result.minimum_core_usage_percent == 10.0
    assert result.maximum_core_usage_percent == 45.0

def test_cpu_info_accepts_missing_frequency() -> None:
    adapter = LinuxSystemAdapter()

    with (
        patch(
            "app.adapters.linux.linux_system_adapter."
            "psutil.cpu_percent",
            side_effect=[
                10.0,
                [
                    5.0,
                    10.0,
                    15.0,
                    20.0,
                    25.0,
                    30.0,
                    35.0,
                    40.0,
                ],
            ],
        ),
        patch(
            "app.adapters.linux.linux_system_adapter."
            "psutil.cpu_count",
            side_effect=[8, None],
        ),
        patch(
            "app.adapters.linux.linux_system_adapter."
            "psutil.cpu_freq",
            return_value=None,
        ),
    ):
        result = adapter.cpu_info()

    assert result.logical_cores == 8
    assert result.physical_cores is None
    assert result.frequency_mhz is None
    assert result.per_core_usage_percent == (
        5.0,
        10.0,
        15.0,
        20.0,
        25.0,
        30.0,
        35.0,
        40.0,
    )


def test_memory_info() -> None:
    adapter = LinuxSystemAdapter()

    memory = type(
        "VirtualMemory",
        (),
        {
            "total": 8_000,
            "available": 5_000,
            "used": 3_000,
            "percent": 37.5,
            "free": 2_000,
            "cached": 800,
            "buffers": 200,
        },
    )()

    with patch(
        "app.adapters.linux.linux_system_adapter."
        "psutil.virtual_memory",
        return_value=memory,
    ):
        result = adapter.memory_info()

    assert result.total_bytes == 8_000
    assert result.available_bytes == 5_000
    assert result.used_bytes == 3_000
    assert result.usage_percent == 37.5
    assert result.free_bytes == 2_000
    assert result.cached_bytes == 800
    assert result.buffers_bytes == 200

def test_disk_info() -> None:
    adapter = LinuxSystemAdapter()

    disk = type(
        "DiskUsage",
        (),
        {
            "total": 100_000,
            "used": 40_000,
            "free": 60_000,
            "percent": 40.0,
        },
    )()

    partition = type(
        "Partition",
        (),
        {
            "device": "/dev/sda2",
            "mountpoint": "/",
            "fstype": "ext4",
        },
    )()

    with (
        patch(
            "app.adapters.linux.linux_system_adapter."
            "psutil.disk_usage",
            return_value=disk,
        ) as disk_usage,
        patch(
            "app.adapters.linux.linux_system_adapter."
            "psutil.disk_partitions",
            return_value=[partition],
        ) as disk_partitions,
    ):
        result = adapter.disk_info()

    disk_usage.assert_called_once_with("/")
    disk_partitions.assert_called_once_with(all=False)

    assert result.total_bytes == 100_000
    assert result.used_bytes == 40_000
    assert result.free_bytes == 60_000
    assert result.usage_percent == 40.0
    assert result.device == "/dev/sda2"
    assert result.mount_point == "/"
    assert result.filesystem_type == "ext4"



def test_uptime_info() -> None:
    adapter = LinuxSystemAdapter()

    with (
        patch(
            "app.adapters.linux.linux_system_adapter.time.time",
            return_value=200_000.0,
        ),
        patch(
            "app.adapters.linux.linux_system_adapter."
            "psutil.boot_time",
            return_value=113_600.0,
        ),
    ):
        result = adapter.uptime_info()

    assert result.uptime_seconds == 86_400
def test_map_systemd_running_status() -> None:
    status = LinuxSystemAdapter._map_systemd_status(
        active_state="active",
        sub_state="running",
    )

    assert status is ServiceStatus.RUNNING


def test_map_systemd_failed_status() -> None:
    status = LinuxSystemAdapter._map_systemd_status(
        active_state="failed",
        sub_state="failed",
    )

    assert status is ServiceStatus.FAILED


def test_map_systemd_stopped_status() -> None:
    status = LinuxSystemAdapter._map_systemd_status(
        active_state="inactive",
        sub_state="dead",
    )

    assert status is ServiceStatus.STOPPED


def test_map_systemd_unknown_status() -> None:
    status = LinuxSystemAdapter._map_systemd_status(
        active_state="activating",
        sub_state="start",
    )

    assert status is ServiceStatus.UNKNOWN

def test_process_service_stopped_when_no_process_matches() -> None:
    adapter = LinuxSystemAdapter()

    with patch(
        "app.adapters.linux.linux_system_adapter."
        "psutil.process_iter",
        return_value=[],
    ):
        result = adapter._process_service(
            name="FFmpeg",
            process_name="ffmpeg",
        )

    assert result.name == "FFmpeg"
    assert result.status is ServiceStatus.STOPPED
    assert result.instances == ()


def test_process_service_running_when_process_matches() -> None:
    adapter = LinuxSystemAdapter()

    process = type(
        "FakeProcess",
        (),
        {
            "info": {
                "pid": 1234,
                "name": "uvicorn",
                "cmdline": [
                    "uvicorn",
                    "app.main:app",
                ],
            },
        },
    )()

    with (
        patch(
            "app.adapters.linux.linux_system_adapter."
            "psutil.process_iter",
            return_value=[process],
        ),
        patch.object(
            adapter,
            "_process_instance",
            return_value=ServiceInstance(
                pid=1234,
                cpu_percent=1.5,
                memory_bytes=50_000_000,
                uptime_seconds=120,
            ),
        ),
    ):
        result = adapter._process_service(
            name="Control Center Backend",
            process_name="uvicorn",
        )

    assert result.status is ServiceStatus.RUNNING
    assert len(result.instances) == 1
    assert result.instances[0].pid == 1234

def test_network_info() -> None:
    adapter = LinuxSystemAdapter()

    counters = type(
        "NetworkCounters",
        (),
        {
            "bytes_sent": 1_000_000,
            "bytes_recv": 2_000_000,
            "packets_sent": 10_000,
            "packets_recv": 20_000,
            "errin": 2,
            "errout": 1,
            "dropin": 4,
            "dropout": 3,
        },
    )()

    with patch(
        "app.adapters.linux.linux_system_adapter."
        "psutil.net_io_counters",
        return_value={"ens2f0": counters},
    ) as net_io_counters:
        result = adapter.network_info("ens2f0")

    net_io_counters.assert_called_once_with(pernic=True)

    assert result.interface == "ens2f0"
    assert result.bytes_sent == 1_000_000
    assert result.bytes_received == 2_000_000
    assert result.packets_sent == 10_000
    assert result.packets_received == 20_000
    assert result.errors_in == 2
    assert result.errors_out == 1
    assert result.dropped_in == 4
    assert result.dropped_out == 3

def test_network_info_rejects_unknown_interface() -> None:
    adapter = LinuxSystemAdapter()

    with patch(
        "app.adapters.linux.linux_system_adapter."
        "psutil.net_io_counters",
        return_value={},
    ):
        with pytest.raises(ValueError):
            adapter.network_info("ens2f0")