"""Tests for NetworkInterfaceHealth."""

from datetime import UTC, datetime, timedelta

import pytest

from app.noc.domain.network_interface_health import (
    NetworkInterfaceHealth,
)
from app.noc.domain.node_health import NodeHealthState


def make_health(
    **overrides,
) -> NetworkInterfaceHealth:
    values = {
        "interface": "ens2f0",
        "state": NodeHealthState.HEALTHY,
        "observed_at": datetime(
            2026,
            8,
            18,
            20,
            30,
            tzinfo=UTC,
        ),
        "reason": "Interface operating normally",
        "carrier_ok": True,
        "traffic_ok": True,
        "error_rate": 0.0,
        "drop_rate": 0.0,
    }

    values.update(overrides)

    return NetworkInterfaceHealth(**values)


def test_network_interface_health_can_be_created() -> None:
    health = make_health()

    assert health.interface == "ens2f0"
    assert health.state is NodeHealthState.HEALTHY
    assert health.is_healthy is True
    assert health.requires_attention is False


@pytest.mark.parametrize(
    "state",
    (
        NodeHealthState.WARNING,
        NodeHealthState.DEGRADED,
        NodeHealthState.CRITICAL,
    ),
)
def test_non_healthy_known_states_require_attention(
    state: NodeHealthState,
) -> None:
    health = make_health(
        state=state,
    )

    assert health.requires_attention is True


def test_unknown_does_not_require_attention() -> None:
    health = make_health(
        state=NodeHealthState.UNKNOWN,
    )

    assert health.requires_attention is False


def test_interface_is_normalized() -> None:
    health = make_health(
        interface="  enp9s0  ",
    )

    assert health.interface == "enp9s0"


@pytest.mark.parametrize(
    "interface",
    (
        "",
        "   ",
    ),
)
def test_empty_interface_is_rejected(
    interface: str,
) -> None:
    with pytest.raises(ValueError):
        make_health(
            interface=interface,
        )


def test_invalid_state_is_rejected() -> None:
    with pytest.raises(TypeError):
        make_health(
            state="HEALTHY",
        )


def test_naive_observed_at_is_rejected() -> None:
    with pytest.raises(ValueError):
        make_health(
            observed_at=datetime(
                2026,
                8,
                18,
                20,
                30,
            ),
        )


def test_non_utc_observed_at_is_rejected() -> None:
    with pytest.raises(ValueError):
        make_health(
            observed_at=datetime(
                2026,
                8,
                18,
                20,
                30,
                tzinfo=timezone_offset(),
            ),
        )


def timezone_offset():
    return UTC_PLUS_ONE


UTC_PLUS_ONE = __import__(
    "datetime"
).timezone(
    timedelta(hours=1)
)


@pytest.mark.parametrize(
    "name",
    (
        "carrier_ok",
        "traffic_ok",
    ),
)
def test_boolean_fields_reject_non_boolean(
    name: str,
) -> None:
    with pytest.raises(TypeError):
        make_health(
            **{name: 1},
        )


@pytest.mark.parametrize(
    "name",
    (
        "error_rate",
        "drop_rate",
    ),
)
def test_rates_reject_negative_values(
    name: str,
) -> None:
    with pytest.raises(ValueError):
        make_health(
            **{name: -0.1},
        )


def test_rates_are_normalized_to_float() -> None:
    health = make_health(
        error_rate=2,
        drop_rate=3,
    )

    assert health.error_rate == 2.0
    assert health.drop_rate == 3.0
