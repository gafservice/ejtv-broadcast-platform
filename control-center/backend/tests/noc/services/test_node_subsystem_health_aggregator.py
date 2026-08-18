"""Tests for NodeSubsystemHealthAggregator."""

import pytest

from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.services.node_subsystem_health_aggregator import (
    NodeSubsystemHealthAggregator,
)


def health(
    state: NodeHealthState,
) -> NodeHealth:
    return NodeHealth(state)


@pytest.mark.parametrize(
    ("states", "expected"),
    (
        (
            (
                NodeHealthState.HEALTHY,
                NodeHealthState.HEALTHY,
            ),
            NodeHealthState.HEALTHY,
        ),
        (
            (
                NodeHealthState.HEALTHY,
                NodeHealthState.WARNING,
            ),
            NodeHealthState.WARNING,
        ),
        (
            (
                NodeHealthState.WARNING,
                NodeHealthState.DEGRADED,
            ),
            NodeHealthState.DEGRADED,
        ),
        (
            (
                NodeHealthState.HEALTHY,
                NodeHealthState.CRITICAL,
            ),
            NodeHealthState.CRITICAL,
        ),
        (
            (
                NodeHealthState.WARNING,
                NodeHealthState.CRITICAL,
                NodeHealthState.DEGRADED,
            ),
            NodeHealthState.CRITICAL,
        ),
    ),
)
def test_aggregate_returns_worst_known_state(
    states: tuple[NodeHealthState, ...],
    expected: NodeHealthState,
) -> None:
    result = NodeSubsystemHealthAggregator().aggregate(
        tuple(
            health(state)
            for state in states
        )
    )

    assert result.state is expected


def test_empty_collection_returns_unknown() -> None:
    result = NodeSubsystemHealthAggregator().aggregate(())

    assert result.state is NodeHealthState.UNKNOWN


def test_all_unknown_returns_unknown() -> None:
    result = NodeSubsystemHealthAggregator().aggregate(
        (
            health(NodeHealthState.UNKNOWN),
            health(NodeHealthState.UNKNOWN),
        )
    )

    assert result.state is NodeHealthState.UNKNOWN


def test_unknown_does_not_override_healthy() -> None:
    result = NodeSubsystemHealthAggregator().aggregate(
        (
            health(NodeHealthState.UNKNOWN),
            health(NodeHealthState.HEALTHY),
        )
    )

    assert result.state is NodeHealthState.HEALTHY


def test_unknown_does_not_override_warning() -> None:
    result = NodeSubsystemHealthAggregator().aggregate(
        (
            health(NodeHealthState.UNKNOWN),
            health(NodeHealthState.WARNING),
        )
    )

    assert result.state is NodeHealthState.WARNING


def test_unknown_does_not_hide_critical() -> None:
    result = NodeSubsystemHealthAggregator().aggregate(
        (
            health(NodeHealthState.UNKNOWN),
            health(NodeHealthState.CRITICAL),
        )
    )

    assert result.state is NodeHealthState.CRITICAL


def test_aggregate_requires_tuple() -> None:
    with pytest.raises(TypeError):
        NodeSubsystemHealthAggregator().aggregate(
            []  # type: ignore[arg-type]
        )


def test_aggregate_rejects_non_health_entry() -> None:
    with pytest.raises(TypeError):
        NodeSubsystemHealthAggregator().aggregate(
            (
                health(NodeHealthState.HEALTHY),
                object(),  # type: ignore[arg-type]
            )
        )
