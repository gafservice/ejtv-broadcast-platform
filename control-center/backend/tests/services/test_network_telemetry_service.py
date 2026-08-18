"""Tests para NetworkTelemetryService."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    NetworkInfo,
    NetworkInterfaceInfo,
    NetworkInterfaceType,
    SystemResources,
    UptimeInfo,
)
from app.services.network_telemetry_service import (
    NetworkTelemetryService,
)


def make_network(
    interface: str,
    *,
    received: int,
    sent: int,
) -> NetworkInfo:
    return NetworkInfo(
        interface=interface,
        bytes_sent=sent,
        bytes_received=received,
        packets_sent=10,
        packets_received=20,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )


def make_info(
    interface: str,
) -> NetworkInterfaceInfo:
    return NetworkInterfaceInfo(
        interface=interface,
        interface_type=NetworkInterfaceType.ETHERNET,
        is_up=True,
        carrier=True,
        mtu=1500,
        link_speed_mbps=1000,
    )


def make_resources(
    captured_at: datetime,
    networks: tuple[NetworkInfo, ...],
) -> SystemResources:
    return SystemResources(
        cpu=CPUInfo(
            usage_percent=10,
            logical_cores=4,
            physical_cores=2,
            frequency_mhz=2800,
        ),
        memory=MemoryInfo(
            total_bytes=8_000,
            available_bytes=4_000,
            used_bytes=4_000,
            usage_percent=50,
        ),
        disk=DiskInfo(
            total_bytes=100_000,
            used_bytes=40_000,
            free_bytes=60_000,
            usage_percent=40,
        ),
        network=networks[0],
        networks=networks,
        uptime=UptimeInfo(
            uptime_seconds=100,
        ),
        captured_at=captured_at,
    )


def test_builds_multi_interface_telemetry() -> None:
    captured_at = datetime(
        2026,
        8,
        18,
        18,
        0,
        tzinfo=UTC,
    )

    previous_networks = (
        make_network(
            "ens2f0",
            received=1_000,
            sent=500,
        ),
        make_network(
            "enp9s0",
            received=2_000,
            sent=1_000,
        ),
    )

    current_networks = (
        make_network(
            "ens2f0",
            received=3_000,
            sent=1_500,
        ),
        make_network(
            "enp9s0",
            received=6_000,
            sent=3_000,
        ),
    )

    previous = make_resources(
        captured_at,
        previous_networks,
    )

    current = make_resources(
        captured_at + timedelta(seconds=2),
        current_networks,
    )

    result = NetworkTelemetryService().build(
        previous=previous,
        current=current,
        interface_infos=(
            make_info("ens2f0"),
            make_info("enp9s0"),
        ),
    )

    assert len(result) == 2

    assert tuple(
        telemetry.interface
        for telemetry in result
    ) == (
        "ens2f0",
        "enp9s0",
    )

    assert result[0].rates is not None
    assert result[0].rates.rx_bps == 8_000.0
    assert result[0].rates.tx_bps == 4_000.0

    assert result[1].rates is not None
    assert result[1].rates.rx_bps == 16_000.0
    assert result[1].rates.tx_bps == 8_000.0


def test_first_capture_builds_telemetry_without_rates() -> None:
    captured_at = datetime(
        2026,
        8,
        18,
        18,
        0,
        tzinfo=UTC,
    )

    networks = (
        make_network(
            "ens2f0",
            received=1_000,
            sent=500,
        ),
    )

    current = make_resources(
        captured_at,
        networks,
    )

    result = NetworkTelemetryService().build(
        previous=None,
        current=current,
        interface_infos=(
            make_info("ens2f0"),
        ),
    )

    assert len(result) == 1
    assert result[0].rates is not None
    assert result[0].rates.rx_bps is None
    assert result[0].rates.tx_bps is None


def test_rejects_missing_interface_info() -> None:
    captured_at = datetime(
        2026,
        8,
        18,
        18,
        0,
        tzinfo=UTC,
    )

    networks = (
        make_network(
            "ens2f0",
            received=1_000,
            sent=500,
        ),
        make_network(
            "enp9s0",
            received=2_000,
            sent=1_000,
        ),
    )

    current = make_resources(
        captured_at,
        networks,
    )

    with pytest.raises(
        ValueError,
        match="enp9s0",
    ):
        NetworkTelemetryService().build(
            previous=None,
            current=current,
            interface_infos=(
                make_info("ens2f0"),
            ),
        )
