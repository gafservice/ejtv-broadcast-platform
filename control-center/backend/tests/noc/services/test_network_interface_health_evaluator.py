"""Tests for NetworkInterfaceHealthEvaluator."""

from datetime import UTC, datetime

import pytest

from app.domain.system import (
    NetworkInfo,
    NetworkInterfaceInfo,
    NetworkInterfaceTelemetry,
    NetworkInterfaceType,
    NetworkRate,
)
from app.noc.domain.node_health import NodeHealthState
from app.noc.services.network_interface_health_evaluator import (
    NetworkInterfaceHealthEvaluator,
)


CAPTURED_AT = datetime(
    2026,
    8,
    18,
    21,
    0,
    tzinfo=UTC,
)


def make_info(
    *,
    is_up: bool = True,
    carrier: bool | None = True,
) -> NetworkInterfaceInfo:
    return NetworkInterfaceInfo(
        interface="ens2f0",
        interface_type=NetworkInterfaceType.ETHERNET,
        is_up=is_up,
        carrier=carrier,
        mtu=1500,
        link_speed_mbps=1000,
    )


def make_counters() -> NetworkInfo:
    return NetworkInfo(
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


def make_rate(
    *,
    rx_bps: float | None = 1_000_000.0,
    tx_bps: float | None = 2_000_000.0,
    errors_in_per_second: float | None = 0.0,
    errors_out_per_second: float | None = 0.0,
    dropped_in_per_second: float | None = 0.0,
    dropped_out_per_second: float | None = 0.0,
    interval_seconds: float | None = 1.0,
) -> NetworkRate:
    return NetworkRate(
        interface="ens2f0",
        rx_bps=rx_bps,
        tx_bps=tx_bps,
        interval_seconds=interval_seconds,
        errors_in=0,
        errors_out=0,
        dropped_in=0,
        dropped_out=0,
        captured_at=CAPTURED_AT,
        errors_in_per_second=errors_in_per_second,
        errors_out_per_second=errors_out_per_second,
        dropped_in_per_second=dropped_in_per_second,
        dropped_out_per_second=dropped_out_per_second,
    )


def make_telemetry(
    *,
    info: NetworkInterfaceInfo | None = None,
    rates: NetworkRate | None = None,
) -> NetworkInterfaceTelemetry:
    return NetworkInterfaceTelemetry(
        info=info if info is not None else make_info(),
        counters=make_counters(),
        captured_at=CAPTURED_AT,
        rates=rates,
    )


def test_healthy_interface() -> None:
    result = NetworkInterfaceHealthEvaluator().evaluate(
        make_telemetry(
            rates=make_rate(),
        )
    )

    assert result.state is NodeHealthState.HEALTHY
    assert result.interface == "ens2f0"
    assert result.observed_at == CAPTURED_AT
    assert result.carrier_ok is True
    assert result.traffic_ok is True
    assert result.error_rate == 0.0
    assert result.drop_rate == 0.0


def test_warning_on_elevated_drop_rate() -> None:
    result = NetworkInterfaceHealthEvaluator().evaluate(
        make_telemetry(
            rates=make_rate(
                dropped_in_per_second=1.5,
            ),
        )
    )

    assert result.state is NodeHealthState.WARNING
    assert result.drop_rate == 1.5


def test_degraded_on_high_error_rate() -> None:
    result = NetworkInterfaceHealthEvaluator().evaluate(
        make_telemetry(
            rates=make_rate(
                errors_in_per_second=7.0,
                errors_out_per_second=4.0,
            ),
        )
    )

    assert result.state is NodeHealthState.DEGRADED
    assert result.error_rate == 11.0


def test_critical_when_up_without_carrier() -> None:
    result = NetworkInterfaceHealthEvaluator().evaluate(
        make_telemetry(
            info=make_info(
                is_up=True,
                carrier=False,
            ),
            rates=make_rate(),
        )
    )

    assert result.state is NodeHealthState.CRITICAL
    assert result.carrier_ok is False


def test_down_interface_is_unknown_without_role_policy() -> None:
    result = NetworkInterfaceHealthEvaluator().evaluate(
        make_telemetry(
            info=make_info(
                is_up=False,
                carrier=False,
            ),
            rates=make_rate(),
        )
    )

    assert result.state is NodeHealthState.UNKNOWN
    assert result.observed_at == CAPTURED_AT


def test_first_capture_is_unknown() -> None:
    result = NetworkInterfaceHealthEvaluator().evaluate(
        make_telemetry(
            rates=None,
        )
    )

    assert result.state is NodeHealthState.UNKNOWN
    assert result.observed_at == CAPTURED_AT


def test_missing_quality_rates_is_unknown() -> None:
    result = NetworkInterfaceHealthEvaluator().evaluate(
        make_telemetry(
            rates=make_rate(
                errors_in_per_second=None,
            ),
        )
    )

    assert result.state is NodeHealthState.UNKNOWN


def test_zero_traffic_does_not_make_interface_unhealthy() -> None:
    result = NetworkInterfaceHealthEvaluator().evaluate(
        make_telemetry(
            rates=make_rate(
                rx_bps=0.0,
                tx_bps=0.0,
            ),
        )
    )

    assert result.state is NodeHealthState.HEALTHY
    assert result.traffic_ok is True


def test_rejects_invalid_telemetry_type() -> None:
    with pytest.raises(TypeError):
        NetworkInterfaceHealthEvaluator().evaluate(
            object()  # type: ignore[arg-type]
        )
