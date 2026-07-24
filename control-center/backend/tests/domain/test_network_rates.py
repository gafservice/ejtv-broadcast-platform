"""Pruebas del cálculo de tasas de transferencia de red."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    NetworkInfo,
    NetworkRateCalculator,
    SystemResources,
    UptimeInfo,
)


def build_resources(
    *,
    captured_at: datetime,
    interface: str = "ens2f0",
    bytes_received: int = 2_000_000,
    bytes_sent: int = 1_000_000,
    errors_in: int = 0,
    errors_out: int = 0,
    dropped_in: int = 0,
    dropped_out: int = 0,
) -> SystemResources:
    """Construye una captura controlada para las pruebas."""

    return SystemResources(
        cpu=CPUInfo(
            usage_percent=25.0,
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
            interface=interface,
            bytes_sent=bytes_sent,
            bytes_received=bytes_received,
            packets_sent=10_000,
            packets_received=20_000,
            errors_in=errors_in,
            errors_out=errors_out,
            dropped_in=dropped_in,
            dropped_out=dropped_out,
        ),
        uptime=UptimeInfo(
            uptime_seconds=86_400,
        ),
        captured_at=captured_at,
    )


def test_first_capture_has_no_network_rates() -> None:
    """La primera captura no permite calcular una tasa."""

    current = build_resources(
        captured_at=datetime(2026, 7, 24, 12, 0, tzinfo=UTC),
    )

    result = NetworkRateCalculator().compare(None, current)

    assert result.interface == "ens2f0"
    assert result.rx_bps is None
    assert result.tx_bps is None
    assert result.interval_seconds is None


def test_calculates_network_rates_from_two_captures() -> None:
    """Debe calcular bits por segundo usando diferencias de bytes."""

    captured_at = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)

    previous = build_resources(
        captured_at=captured_at,
        bytes_received=2_000_000,
        bytes_sent=1_000_000,
    )

    current = build_resources(
        captured_at=captured_at + timedelta(seconds=2),
        bytes_received=3_000_000,
        bytes_sent=1_500_000,
    )

    result = NetworkRateCalculator().compare(
        previous,
        current,
    )

    assert result.interval_seconds == 2.0
    assert result.rx_bps == 4_000_000.0
    assert result.tx_bps == 2_000_000.0


def test_interface_change_makes_rates_unavailable() -> None:
    """No debe comparar contadores de interfaces diferentes."""

    captured_at = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)

    previous = build_resources(
        captured_at=captured_at,
        interface="ens2f0",
    )

    current = build_resources(
        captured_at=captured_at + timedelta(seconds=1),
        interface="ens2f1",
    )

    result = NetworkRateCalculator().compare(
        previous,
        current,
    )

    assert result.rx_bps is None
    assert result.tx_bps is None
    assert result.interval_seconds is None


@pytest.mark.parametrize(
    "seconds",
    [0, -1],
)
def test_invalid_time_interval_makes_rates_unavailable(
    seconds: int,
) -> None:
    """Un tiempo igual o anterior no debe producir tasas."""

    captured_at = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)

    previous = build_resources(
        captured_at=captured_at,
    )

    current = build_resources(
        captured_at=captured_at + timedelta(seconds=seconds),
        bytes_received=3_000_000,
        bytes_sent=2_000_000,
    )

    result = NetworkRateCalculator().compare(
        previous,
        current,
    )

    assert result.rx_bps is None
    assert result.tx_bps is None
    assert result.interval_seconds is None


def test_counter_reset_makes_rates_unavailable() -> None:
    """Una reducción de contadores indica reinicio o reemplazo."""

    captured_at = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)

    previous = build_resources(
        captured_at=captured_at,
        bytes_received=2_000_000,
        bytes_sent=1_000_000,
    )

    current = build_resources(
        captured_at=captured_at + timedelta(seconds=1),
        bytes_received=100,
        bytes_sent=50,
    )

    result = NetworkRateCalculator().compare(
        previous,
        current,
    )

    assert result.rx_bps is None
    assert result.tx_bps is None
    assert result.interval_seconds is None


def test_uses_current_error_and_drop_counters() -> None:
    """Los contadores operativos deben proceder de la captura actual."""

    captured_at = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)

    previous = build_resources(
        captured_at=captured_at,
    )

    current = build_resources(
        captured_at=captured_at + timedelta(seconds=1),
        bytes_received=2_100_000,
        bytes_sent=1_100_000,
        errors_in=2,
        errors_out=3,
        dropped_in=4,
        dropped_out=5,
    )

    result = NetworkRateCalculator().compare(
        previous,
        current,
    )

    assert result.errors_in == 2
    assert result.errors_out == 3
    assert result.dropped_in == 4
    assert result.dropped_out == 5
