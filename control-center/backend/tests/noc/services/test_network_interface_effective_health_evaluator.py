"""Tests for policy-aware network interface health."""

from datetime import UTC, datetime

import pytest

from app.noc.domain.network_interface_health import (
    NetworkInterfaceHealth,
)
from app.noc.domain.network_interface_policy import (
    NetworkInterfacePolicy,
    NetworkInterfaceRole,
)
from app.noc.domain.node_health import NodeHealthState
from app.noc.services.network_interface_effective_health_evaluator import (
    NetworkInterfaceEffectiveHealthEvaluator,
)


OBSERVED_AT = datetime(
    2026,
    8,
    18,
    21,
    30,
    tzinfo=UTC,
)


def make_health(
    state: NodeHealthState,
    *,
    interface: str = "ens2f1",
    carrier_ok: bool | None = False,
) -> NetworkInterfaceHealth:
    return NetworkInterfaceHealth(
        interface=interface,
        state=state,
        observed_at=OBSERVED_AT,
        reason="Observed state",
        carrier_ok=carrier_ok,
        traffic_ok=None,
        error_rate=None,
        drop_rate=None,
    )


def make_policy(
    *,
    interface: str = "ens2f1",
    expected_up: bool,
    critical: bool,
    role: NetworkInterfaceRole = NetworkInterfaceRole.BACKUP,
) -> NetworkInterfacePolicy:
    return NetworkInterfacePolicy(
        interface=interface,
        role=role,
        expected_up=expected_up,
        critical=critical,
    )


def test_optional_unknown_interface_becomes_healthy() -> None:
    result = NetworkInterfaceEffectiveHealthEvaluator().evaluate(
        make_health(NodeHealthState.UNKNOWN),
        make_policy(
            expected_up=False,
            critical=False,
        ),
    )

    assert result.state is NodeHealthState.HEALTHY
    assert result.observed_at == OBSERVED_AT


def test_required_critical_unknown_without_carrier_becomes_critical() -> None:
    result = NetworkInterfaceEffectiveHealthEvaluator().evaluate(
        make_health(
            NodeHealthState.UNKNOWN,
            interface="enp9s0",
        ),
        make_policy(
            interface="enp9s0",
            expected_up=True,
            critical=True,
            role=NetworkInterfaceRole.INGEST,
        ),
    )

    assert result.state is NodeHealthState.CRITICAL


def test_required_noncritical_unknown_without_carrier_becomes_degraded() -> None:
    result = NetworkInterfaceEffectiveHealthEvaluator().evaluate(
        make_health(NodeHealthState.UNKNOWN),
        make_policy(
            expected_up=True,
            critical=False,
        ),
    )

    assert result.state is NodeHealthState.DEGRADED




def test_required_critical_unknown_with_carrier_remains_unknown() -> None:
    observed = make_health(
        NodeHealthState.UNKNOWN,
        interface="enp9s0",
        carrier_ok=True,
    )

    result = NetworkInterfaceEffectiveHealthEvaluator().evaluate(
        observed,
        make_policy(
            interface="enp9s0",
            expected_up=True,
            critical=True,
            role=NetworkInterfaceRole.INGEST,
        ),
    )

    assert result is observed
    assert result.state is NodeHealthState.UNKNOWN


def test_required_noncritical_unknown_with_carrier_remains_unknown() -> None:
    observed = make_health(
        NodeHealthState.UNKNOWN,
        carrier_ok=True,
    )

    result = NetworkInterfaceEffectiveHealthEvaluator().evaluate(
        observed,
        make_policy(
            expected_up=True,
            critical=False,
        ),
    )

    assert result is observed
    assert result.state is NodeHealthState.UNKNOWN


def test_required_unknown_with_unknown_carrier_remains_unknown() -> None:
    observed = make_health(
        NodeHealthState.UNKNOWN,
        interface="enp9s0",
        carrier_ok=None,
    )

    result = NetworkInterfaceEffectiveHealthEvaluator().evaluate(
        observed,
        make_policy(
            interface="enp9s0",
            expected_up=True,
            critical=True,
            role=NetworkInterfaceRole.INGEST,
        ),
    )

    assert result is observed
    assert result.state is NodeHealthState.UNKNOWN


@pytest.mark.parametrize(
    "state",
    (
        NodeHealthState.HEALTHY,
        NodeHealthState.WARNING,
        NodeHealthState.DEGRADED,
        NodeHealthState.CRITICAL,
    ),
)
def test_known_observed_state_is_preserved(
    state: NodeHealthState,
) -> None:
    observed = make_health(state)

    result = NetworkInterfaceEffectiveHealthEvaluator().evaluate(
        observed,
        make_policy(
            expected_up=False,
            critical=False,
        ),
    )

    assert result is observed


def test_rejects_interface_mismatch() -> None:
    with pytest.raises(ValueError):
        NetworkInterfaceEffectiveHealthEvaluator().evaluate(
            make_health(
                NodeHealthState.UNKNOWN,
                interface="ens2f1",
            ),
            make_policy(
                interface="enp9s0",
                expected_up=True,
                critical=True,
            ),
        )


def test_rejects_invalid_observed_type() -> None:
    with pytest.raises(TypeError):
        NetworkInterfaceEffectiveHealthEvaluator().evaluate(
            object(),  # type: ignore[arg-type]
            make_policy(
                expected_up=False,
                critical=False,
            ),
        )


def test_rejects_invalid_policy_type() -> None:
    with pytest.raises(TypeError):
        NetworkInterfaceEffectiveHealthEvaluator().evaluate(
            make_health(NodeHealthState.UNKNOWN),
            object(),  # type: ignore[arg-type]
        )
