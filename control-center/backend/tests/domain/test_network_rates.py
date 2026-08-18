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


def test_calculates_network_quality_rates() -> None:
    captured_at = datetime(
        2026,
        8,
        17,
        23,
        0,
        tzinfo=UTC,
    )

    previous = build_resources(
        captured_at=captured_at,
        errors_in=10,
        errors_out=20,
        dropped_in=100,
        dropped_out=50,
    )

    current = build_resources(
        captured_at=captured_at + timedelta(seconds=5),
        bytes_received=2_100_000,
        bytes_sent=1_100_000,
        errors_in=15,
        errors_out=30,
        dropped_in=130,
        dropped_out=60,
    )

    result = NetworkRateCalculator().compare(
        previous,
        current,
    )

    assert result.errors_in_per_second == 1.0
    assert result.errors_out_per_second == 2.0
    assert result.dropped_in_per_second == 6.0
    assert result.dropped_out_per_second == 2.0


def test_unchanged_quality_counters_produce_zero_rates() -> None:
    captured_at = datetime(
        2026,
        8,
        17,
        23,
        0,
        tzinfo=UTC,
    )

    previous = build_resources(
        captured_at=captured_at,
        errors_in=10,
        errors_out=20,
        dropped_in=100,
        dropped_out=50,
    )

    current = build_resources(
        captured_at=captured_at + timedelta(seconds=5),
        bytes_received=2_100_000,
        bytes_sent=1_100_000,
        errors_in=10,
        errors_out=20,
        dropped_in=100,
        dropped_out=50,
    )

    result = NetworkRateCalculator().compare(
        previous,
        current,
    )

    assert result.errors_in_per_second == 0.0
    assert result.errors_out_per_second == 0.0
    assert result.dropped_in_per_second == 0.0
    assert result.dropped_out_per_second == 0.0


def test_quality_counter_reset_makes_quality_rates_unavailable() -> None:
    captured_at = datetime(
        2026,
        8,
        17,
        23,
        0,
        tzinfo=UTC,
    )

    previous = build_resources(
        captured_at=captured_at,
        errors_in=10,
        errors_out=20,
        dropped_in=100,
        dropped_out=50,
    )

    current = build_resources(
        captured_at=captured_at + timedelta(seconds=5),
        bytes_received=2_100_000,
        bytes_sent=1_100_000,
        errors_in=1,
        errors_out=2,
        dropped_in=10,
        dropped_out=5,
    )

    result = NetworkRateCalculator().compare(
        previous,
        current,
    )

    assert result.errors_in_per_second is None
    assert result.errors_out_per_second is None
    assert result.dropped_in_per_second is None
    assert result.dropped_out_per_second is None


def test_compare_interface_calculates_independent_rate() -> None:
    captured_at = datetime(
        2026,
        8,
        18,
        18,
        0,
        tzinfo=UTC,
    )

    previous = NetworkInfo(
        interface="enp9s0",
        bytes_sent=1_000,
        bytes_received=2_000,
        packets_sent=10,
        packets_received=20,
        errors_in=1,
        errors_out=2,
        dropped_in=3,
        dropped_out=4,
    )

    current = NetworkInfo(
        interface="enp9s0",
        bytes_sent=2_000,
        bytes_received=4_000,
        packets_sent=20,
        packets_received=40,
        errors_in=3,
        errors_out=4,
        dropped_in=7,
        dropped_out=6,
    )

    result = NetworkRateCalculator().compare_interface(
        previous=previous,
        current=current,
        previous_captured_at=captured_at,
        current_captured_at=(
            captured_at + timedelta(seconds=2)
        ),
    )

    assert result.interface == "enp9s0"
    assert result.interval_seconds == 2.0

    assert result.rx_bps == 8_000.0
    assert result.tx_bps == 4_000.0

    assert result.errors_in_per_second == 1.0
    assert result.errors_out_per_second == 1.0
    assert result.dropped_in_per_second == 2.0
    assert result.dropped_out_per_second == 1.0


def test_compare_interface_first_capture_has_no_rates() -> None:
    captured_at = datetime(
        2026,
        8,
        18,
        18,
        0,
        tzinfo=UTC,
    )

    current = NetworkInfo(
        interface="ens2f1",
        bytes_sent=100,
        bytes_received=200,
        packets_sent=1,
        packets_received=2,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )

    result = NetworkRateCalculator().compare_interface(
        previous=None,
        current=current,
        previous_captured_at=None,
        current_captured_at=captured_at,
    )

    assert result.interface == "ens2f1"
    assert result.rx_bps is None
    assert result.tx_bps is None
    assert result.interval_seconds is None


def test_compare_interface_rejects_interface_mismatch_for_rates() -> None:
    captured_at = datetime(
        2026,
        8,
        18,
        18,
        0,
        tzinfo=UTC,
    )

    previous = NetworkInfo(
        interface="enp9s0",
        bytes_sent=100,
        bytes_received=200,
        packets_sent=1,
        packets_received=2,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )

    current = NetworkInfo(
        interface="ens2f0",
        bytes_sent=200,
        bytes_received=400,
        packets_sent=2,
        packets_received=4,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )

    result = NetworkRateCalculator().compare_interface(
        previous=previous,
        current=current,
        previous_captured_at=captured_at,
        current_captured_at=(
            captured_at + timedelta(seconds=1)
        ),
    )

    assert result.interface == "ens2f0"
    assert result.rx_bps is None
    assert result.tx_bps is None
    assert result.interval_seconds is None


def test_compare_interface_requires_previous_timestamp() -> None:
    current = NetworkInfo(
        interface="ens2f0",
        bytes_sent=100,
        bytes_received=200,
        packets_sent=1,
        packets_received=2,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )

    with pytest.raises(ValueError):
        NetworkRateCalculator().compare_interface(
            previous=current,
            current=current,
            previous_captured_at=None,
            current_captured_at=datetime.now(UTC),
        )


def test_multi_network_rate_calculator_calculates_each_interface() -> None:
    from app.domain.system import MultiNetworkRateCalculator

    captured_at = datetime(
        2026,
        8,
        18,
        18,
        0,
        tzinfo=UTC,
    )

    previous_primary = NetworkInfo(
        interface="ens2f0",
        bytes_sent=1_000,
        bytes_received=2_000,
        packets_sent=10,
        packets_received=20,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )

    previous_secondary = NetworkInfo(
        interface="enp9s0",
        bytes_sent=500,
        bytes_received=1_000,
        packets_sent=5,
        packets_received=10,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )

    current_primary = NetworkInfo(
        interface="ens2f0",
        bytes_sent=2_000,
        bytes_received=4_000,
        packets_sent=20,
        packets_received=40,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )

    current_secondary = NetworkInfo(
        interface="enp9s0",
        bytes_sent=1_500,
        bytes_received=3_000,
        packets_sent=15,
        packets_received=30,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )

    previous = build_resources(
        captured_at=captured_at,
    )

    previous = SystemResources(
        cpu=previous.cpu,
        memory=previous.memory,
        disk=previous.disk,
        network=previous_primary,
        uptime=previous.uptime,
        captured_at=previous.captured_at,
        networks=(
            previous_secondary,
            previous_primary,
        ),
    )

    current = build_resources(
        captured_at=(
            captured_at + timedelta(seconds=2)
        ),
    )

    current = SystemResources(
        cpu=current.cpu,
        memory=current.memory,
        disk=current.disk,
        network=current_primary,
        uptime=current.uptime,
        captured_at=current.captured_at,
        networks=(
            current_secondary,
            current_primary,
        ),
    )

    rates = MultiNetworkRateCalculator().compare(
        previous,
        current,
    )

    assert tuple(
        rate.interface
        for rate in rates
    ) == (
        "enp9s0",
        "ens2f0",
    )

    assert rates[0].rx_bps == 8_000.0
    assert rates[0].tx_bps == 4_000.0

    assert rates[1].rx_bps == 8_000.0
    assert rates[1].tx_bps == 4_000.0


def test_multi_network_rate_calculator_handles_new_interface() -> None:
    from app.domain.system import MultiNetworkRateCalculator

    captured_at = datetime(
        2026,
        8,
        18,
        18,
        0,
        tzinfo=UTC,
    )

    previous = build_resources(
        captured_at=captured_at,
    )

    current_primary = previous.network

    new_interface = NetworkInfo(
        interface="wlp3s0",
        bytes_sent=100,
        bytes_received=200,
        packets_sent=1,
        packets_received=2,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )

    current = SystemResources(
        cpu=previous.cpu,
        memory=previous.memory,
        disk=previous.disk,
        network=current_primary,
        uptime=previous.uptime,
        captured_at=(
            captured_at + timedelta(seconds=1)
        ),
        networks=(
            current_primary,
            new_interface,
        ),
    )

    rates = MultiNetworkRateCalculator().compare(
        previous,
        current,
    )

    by_interface = {
        rate.interface: rate
        for rate in rates
    }

    assert by_interface["wlp3s0"].rx_bps is None
    assert by_interface["wlp3s0"].tx_bps is None
    assert by_interface["wlp3s0"].interval_seconds is None


def test_multi_network_rate_calculator_first_capture() -> None:
    from app.domain.system import MultiNetworkRateCalculator

    current = build_resources(
        captured_at=datetime(
            2026,
            8,
            18,
            18,
            0,
            tzinfo=UTC,
        ),
    )

    rates = MultiNetworkRateCalculator().compare(
        None,
        current,
    )

    assert len(rates) == len(current.networks)

    assert all(
        rate.rx_bps is None
        and rate.tx_bps is None
        and rate.interval_seconds is None
        for rate in rates
    )
