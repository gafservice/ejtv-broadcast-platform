"""Tests for temporal network-interface health stabilization."""

from datetime import UTC, datetime, timedelta

import pytest

from app.noc.domain.network_interface_health import (
    NetworkInterfaceHealth,
)
from app.noc.domain.node_health import NodeHealthState
from app.noc.services.network_interface_health_stabilizer import (
    NetworkInterfaceHealthStabilizer,
)


BASE_TIME = datetime(
    2026,
    8,
    20,
    22,
    30,
    tzinfo=UTC,
)


def make_health(
    state: NodeHealthState,
    *,
    seconds: float = 0.0,
    interface: str = "enp9s0",
) -> NetworkInterfaceHealth:
    return NetworkInterfaceHealth(
        interface=interface,
        state=state,
        observed_at=BASE_TIME + timedelta(seconds=seconds),
        reason=f"Observed {state.value}",
        carrier_ok=True,
        traffic_ok=True,
        error_rate=0.0,
        drop_rate=0.0,
    )


def test_first_observation_becomes_stable_immediately() -> None:
    stabilizer = NetworkInterfaceHealthStabilizer()

    health = make_health(
        NodeHealthState.HEALTHY,
    )

    assert stabilizer.stabilize(health) is health


def test_warning_spike_does_not_replace_healthy_state() -> None:
    stabilizer = NetworkInterfaceHealthStabilizer(
        degradation_seconds=3.0,
    )

    healthy = make_health(
        NodeHealthState.HEALTHY,
        seconds=0,
    )

    warning = make_health(
        NodeHealthState.WARNING,
        seconds=1,
    )

    assert stabilizer.stabilize(healthy) is healthy
    result = stabilizer.stabilize(warning)

    assert result.state is NodeHealthState.HEALTHY
    assert result.observed_at == warning.observed_at
    assert result.error_rate == warning.error_rate
    assert result.drop_rate == warning.drop_rate


def test_warning_commits_after_degradation_delay() -> None:
    stabilizer = NetworkInterfaceHealthStabilizer(
        degradation_seconds=3.0,
    )

    healthy = make_health(
        NodeHealthState.HEALTHY,
        seconds=0,
    )

    warning_1 = make_health(
        NodeHealthState.WARNING,
        seconds=1,
    )

    warning_2 = make_health(
        NodeHealthState.WARNING,
        seconds=4,
    )

    stabilizer.stabilize(healthy)

    result = stabilizer.stabilize(warning_1)

    assert result.state is NodeHealthState.HEALTHY
    assert result.observed_at == warning_1.observed_at
    assert stabilizer.stabilize(warning_2) is warning_2


def test_candidate_is_cancelled_when_stable_state_returns() -> None:
    stabilizer = NetworkInterfaceHealthStabilizer(
        degradation_seconds=3.0,
    )

    healthy_0 = make_health(
        NodeHealthState.HEALTHY,
        seconds=0,
    )

    warning = make_health(
        NodeHealthState.WARNING,
        seconds=1,
    )

    healthy_2 = make_health(
        NodeHealthState.HEALTHY,
        seconds=2,
    )

    warning_3 = make_health(
        NodeHealthState.WARNING,
        seconds=3,
    )

    warning_5 = make_health(
        NodeHealthState.WARNING,
        seconds=5,
    )

    stabilizer.stabilize(healthy_0)
    result = stabilizer.stabilize(warning)

    assert result.state is NodeHealthState.HEALTHY
    assert result.observed_at == warning.observed_at

    assert (
        stabilizer.stabilize(healthy_2)
        is healthy_2
    )

    result = stabilizer.stabilize(warning_3)

    assert result.state is NodeHealthState.HEALTHY
    assert result.observed_at == warning_3.observed_at

    result = stabilizer.stabilize(warning_5)

    assert result.state is NodeHealthState.HEALTHY
    assert result.observed_at == warning_5.observed_at


def test_critical_transition_is_immediate() -> None:
    stabilizer = NetworkInterfaceHealthStabilizer(
        degradation_seconds=30.0,
    )

    healthy = make_health(
        NodeHealthState.HEALTHY,
        seconds=0,
    )

    critical = make_health(
        NodeHealthState.CRITICAL,
        seconds=1,
    )

    stabilizer.stabilize(healthy)

    assert stabilizer.stabilize(critical) is critical


def test_recovery_requires_longer_confirmation() -> None:
    stabilizer = NetworkInterfaceHealthStabilizer(
        degradation_seconds=3.0,
        recovery_seconds=5.0,
    )

    warning = make_health(
        NodeHealthState.WARNING,
        seconds=0,
    )

    healthy_1 = make_health(
        NodeHealthState.HEALTHY,
        seconds=1,
    )

    healthy_5 = make_health(
        NodeHealthState.HEALTHY,
        seconds=5,
    )

    healthy_6 = make_health(
        NodeHealthState.HEALTHY,
        seconds=6,
    )

    stabilizer.stabilize(warning)

    result = stabilizer.stabilize(healthy_1)

    assert result.state is NodeHealthState.WARNING
    assert result.observed_at == healthy_1.observed_at

    result = stabilizer.stabilize(healthy_5)

    assert result.state is NodeHealthState.WARNING
    assert result.observed_at == healthy_5.observed_at

    assert (
        stabilizer.stabilize(healthy_6)
        is healthy_6
    )


def test_interfaces_have_independent_state() -> None:
    stabilizer = NetworkInterfaceHealthStabilizer(
        degradation_seconds=3.0,
    )

    enp9s0 = make_health(
        NodeHealthState.HEALTHY,
        interface="enp9s0",
    )

    ens2f0 = make_health(
        NodeHealthState.WARNING,
        interface="ens2f0",
    )

    assert stabilizer.stabilize(enp9s0) is enp9s0
    assert stabilizer.stabilize(ens2f0) is ens2f0


def test_reset_interface_forgets_history() -> None:
    stabilizer = NetworkInterfaceHealthStabilizer()

    healthy = make_health(
        NodeHealthState.HEALTHY,
    )

    stabilizer.stabilize(healthy)
    stabilizer.reset("enp9s0")

    warning = make_health(
        NodeHealthState.WARNING,
        seconds=1,
    )

    assert stabilizer.stabilize(warning) is warning


def test_rejects_invalid_health() -> None:
    stabilizer = NetworkInterfaceHealthStabilizer()

    with pytest.raises(TypeError):
        stabilizer.stabilize(
            object(),  # type: ignore[arg-type]
        )


def test_rejects_time_moving_backwards() -> None:
    stabilizer = NetworkInterfaceHealthStabilizer()

    current = make_health(
        NodeHealthState.HEALTHY,
        seconds=10,
    )

    older = make_health(
        NodeHealthState.WARNING,
        seconds=9,
    )

    stabilizer.stabilize(current)

    with pytest.raises(ValueError):
        stabilizer.stabilize(older)


@pytest.mark.parametrize(
    "field_name",
    (
        "degradation_seconds",
        "recovery_seconds",
    ),
)
def test_rejects_negative_delay(
    field_name: str,
) -> None:
    kwargs = {
        "degradation_seconds": 3.0,
        "recovery_seconds": 5.0,
    }

    kwargs[field_name] = -1.0

    with pytest.raises(ValueError):
        NetworkInterfaceHealthStabilizer(**kwargs)


def test_held_state_uses_current_observation_timestamp() -> None:
    stabilizer = NetworkInterfaceHealthStabilizer(
        degradation_seconds=3.0,
    )

    healthy = make_health(
        NodeHealthState.HEALTHY,
        seconds=0,
    )

    warning = NetworkInterfaceHealth(
        interface="enp9s0",
        state=NodeHealthState.WARNING,
        observed_at=BASE_TIME + timedelta(seconds=1),
        reason="Elevated network error or drop rate",
        carrier_ok=True,
        traffic_ok=True,
        error_rate=0.0,
        drop_rate=1.57,
    )

    stabilizer.stabilize(healthy)

    result = stabilizer.stabilize(warning)

    assert result.state is NodeHealthState.HEALTHY
    assert result.observed_at == warning.observed_at

    # La evidencia sigue siendo la del ciclo actual.
    assert result.error_rate == 0.0
    assert result.drop_rate == 1.57

    assert (
        "Temporally stabilized at HEALTHY"
        in result.reason
    )
    assert (
        "Elevated network error or drop rate"
        in result.reason
    )
