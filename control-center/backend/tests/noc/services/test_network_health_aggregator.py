"""Tests for NetworkHealthAggregator."""

from datetime import UTC, datetime

import pytest

from app.noc.domain.network_interface_health import (
    NetworkInterfaceHealth,
)
from app.noc.domain.node_health import (
    NodeHealthState,
)
from app.noc.services.network_health_aggregator import (
    NetworkHealthAggregator,
)


OBSERVED_AT = datetime(
    2026,
    8,
    18,
    22,
    0,
    tzinfo=UTC,
)


def make_health(
    interface: str,
    state: NodeHealthState,
) -> NetworkInterfaceHealth:
    return NetworkInterfaceHealth(
        interface=interface,
        state=state,
        observed_at=OBSERVED_AT,
        reason="Test health state",
        carrier_ok=True,
        traffic_ok=True,
        error_rate=0.0,
        drop_rate=0.0,
    )


def test_empty_collection_is_unknown() -> None:
    result = NetworkHealthAggregator().aggregate(())

    assert result.state is NodeHealthState.UNKNOWN


def test_all_healthy_is_healthy() -> None:
    result = NetworkHealthAggregator().aggregate(
        (
            make_health(
                "enp9s0",
                NodeHealthState.HEALTHY,
            ),
            make_health(
                "ens2f0",
                NodeHealthState.HEALTHY,
            ),
            make_health(
                "ens2f1",
                NodeHealthState.HEALTHY,
            ),
        )
    )

    assert result.state is NodeHealthState.HEALTHY


def test_warning_dominates_healthy() -> None:
    result = NetworkHealthAggregator().aggregate(
        (
            make_health(
                "enp9s0",
                NodeHealthState.HEALTHY,
            ),
            make_health(
                "ens2f0",
                NodeHealthState.WARNING,
            ),
            make_health(
                "ens2f1",
                NodeHealthState.HEALTHY,
            ),
        )
    )

    assert result.state is NodeHealthState.WARNING


def test_degraded_dominates_warning() -> None:
    result = NetworkHealthAggregator().aggregate(
        (
            make_health(
                "enp9s0",
                NodeHealthState.WARNING,
            ),
            make_health(
                "ens2f0",
                NodeHealthState.DEGRADED,
            ),
        )
    )

    assert result.state is NodeHealthState.DEGRADED


def test_critical_dominates_all_known_states() -> None:
    result = NetworkHealthAggregator().aggregate(
        (
            make_health(
                "enp9s0",
                NodeHealthState.HEALTHY,
            ),
            make_health(
                "ens2f0",
                NodeHealthState.WARNING,
            ),
            make_health(
                "ens2f1",
                NodeHealthState.DEGRADED,
            ),
            make_health(
                "enp10s0",
                NodeHealthState.CRITICAL,
            ),
        )
    )

    assert result.state is NodeHealthState.CRITICAL


def test_unknown_does_not_override_known_state() -> None:
    result = NetworkHealthAggregator().aggregate(
        (
            make_health(
                "ens2f1",
                NodeHealthState.UNKNOWN,
            ),
            make_health(
                "enp9s0",
                NodeHealthState.HEALTHY,
            ),
        )
    )

    assert result.state is NodeHealthState.HEALTHY


def test_only_unknown_states_produce_unknown() -> None:
    result = NetworkHealthAggregator().aggregate(
        (
            make_health(
                "ens2f1",
                NodeHealthState.UNKNOWN,
            ),
            make_health(
                "enp10s0",
                NodeHealthState.UNKNOWN,
            ),
        )
    )

    assert result.state is NodeHealthState.UNKNOWN


def test_duplicate_interface_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="ens2f0",
    ):
        NetworkHealthAggregator().aggregate(
            (
                make_health(
                    "ens2f0",
                    NodeHealthState.HEALTHY,
                ),
                make_health(
                    "ens2f0",
                    NodeHealthState.WARNING,
                ),
            )
        )


def test_rejects_non_tuple_collection() -> None:
    with pytest.raises(TypeError):
        NetworkHealthAggregator().aggregate(
            []  # type: ignore[arg-type]
        )


def test_rejects_invalid_entry() -> None:
    with pytest.raises(TypeError):
        NetworkHealthAggregator().aggregate(
            (
                object(),  # type: ignore[arg-type]
            )
        )
