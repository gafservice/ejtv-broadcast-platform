"""Tests para NetworkInterfaceTelemetry."""

from datetime import UTC, datetime

import pytest

from app.domain.system import (
    NetworkInfo,
    NetworkInterfaceInfo,
    NetworkInterfaceTelemetry,
    NetworkInterfaceType,
    NetworkRate,
)


def make_info(
    interface: str = "ens2f0",
) -> NetworkInterfaceInfo:
    return NetworkInterfaceInfo(
        interface=interface,
        interface_type=NetworkInterfaceType.ETHERNET,
        is_up=True,
        carrier=True,
        mtu=1500,
        link_speed_mbps=1000,
    )


def make_counters(
    interface: str = "ens2f0",
) -> NetworkInfo:
    return NetworkInfo(
        interface=interface,
        bytes_sent=1_000,
        bytes_received=2_000,
        packets_sent=10,
        packets_received=20,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
    )


def make_rate(
    interface: str = "ens2f0",
) -> NetworkRate:
    return NetworkRate(
        interface=interface,
        rx_bps=8_000.0,
        tx_bps=4_000.0,
        interval_seconds=1.0,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
        captured_at=datetime.now(UTC),
        errors_in_per_second=0.0,
        errors_out_per_second=0.0,
        dropped_in_per_second=0.0,
        dropped_out_per_second=0.0,
    )


def test_network_interface_telemetry_creation() -> None:
    telemetry = NetworkInterfaceTelemetry(
        info=make_info(),
        counters=make_counters(),
        rates=make_rate(),
    )

    assert telemetry.interface == "ens2f0"
    assert telemetry.info.interface == "ens2f0"
    assert telemetry.counters.interface == "ens2f0"
    assert telemetry.rates is not None
    assert telemetry.rates.interface == "ens2f0"


def test_network_interface_telemetry_accepts_missing_rates() -> None:
    telemetry = NetworkInterfaceTelemetry(
        info=make_info(),
        counters=make_counters(),
    )

    assert telemetry.interface == "ens2f0"
    assert telemetry.rates is None


def test_network_interface_telemetry_rejects_counter_mismatch() -> None:
    with pytest.raises(ValueError):
        NetworkInterfaceTelemetry(
            info=make_info("ens2f0"),
            counters=make_counters("enp9s0"),
        )


def test_network_interface_telemetry_rejects_rate_mismatch() -> None:
    with pytest.raises(ValueError):
        NetworkInterfaceTelemetry(
            info=make_info("ens2f0"),
            counters=make_counters("ens2f0"),
            rates=make_rate("ens2f1"),
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("info", object()),
        ("counters", object()),
        ("rates", object()),
    ),
)
def test_network_interface_telemetry_rejects_invalid_types(
    field_name: str,
    value: object,
) -> None:
    values = {
        "info": make_info(),
        "counters": make_counters(),
        "rates": make_rate(),
    }

    values[field_name] = value

    with pytest.raises(TypeError):
        NetworkInterfaceTelemetry(
            **values,  # type: ignore[arg-type]
        )
