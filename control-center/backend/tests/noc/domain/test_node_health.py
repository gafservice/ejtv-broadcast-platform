"""Tests for NodeHealth.

ENG-013B — Node SDK
NCS reference: 12-NODE-HEALTH.md
"""

import pytest

from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)


def test_node_health_state_contains_canonical_values() -> None:
    expected = {
        "HEALTHY",
        "WARNING",
        "DEGRADED",
        "CRITICAL",
        "UNKNOWN",
    }

    assert {state.value for state in NodeHealthState} == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("HEALTHY", NodeHealthState.HEALTHY),
        ("healthy", NodeHealthState.HEALTHY),
        (" warning ", NodeHealthState.WARNING),
        ("degraded", NodeHealthState.DEGRADED),
        ("critical", NodeHealthState.CRITICAL),
        ("unknown", NodeHealthState.UNKNOWN),
    ],
)
def test_node_health_state_from_value(
    raw: str,
    expected: NodeHealthState,
) -> None:
    assert NodeHealthState.from_value(raw) is expected


def test_node_health_state_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        NodeHealthState.from_value("GOOD")


def test_node_health_state_rejects_empty_value() -> None:
    with pytest.raises(ValueError):
        NodeHealthState.from_value("   ")


def test_node_health_state_rejects_non_string_value() -> None:
    with pytest.raises(TypeError):
        NodeHealthState.from_value(123)  # type: ignore[arg-type]


def test_node_health_can_be_created() -> None:
    health = NodeHealth(NodeHealthState.HEALTHY)

    assert health.state is NodeHealthState.HEALTHY


def test_node_health_from_value() -> None:
    health = NodeHealth.from_value(" critical ")

    assert health.state is NodeHealthState.CRITICAL


def test_node_health_rejects_invalid_state_type() -> None:
    with pytest.raises(TypeError):
        NodeHealth("HEALTHY")  # type: ignore[arg-type]


def test_node_health_is_immutable() -> None:
    health = NodeHealth(NodeHealthState.HEALTHY)

    with pytest.raises(AttributeError):
        health.state = NodeHealthState.CRITICAL  # type: ignore[misc]


@pytest.mark.parametrize(
    ("state", "attribute"),
    [
        (NodeHealthState.HEALTHY, "is_healthy"),
        (NodeHealthState.WARNING, "is_warning"),
        (NodeHealthState.DEGRADED, "is_degraded"),
        (NodeHealthState.CRITICAL, "is_critical"),
        (NodeHealthState.UNKNOWN, "is_unknown"),
    ],
)
def test_node_health_state_flags(
    state: NodeHealthState,
    attribute: str,
) -> None:
    health = NodeHealth(state)

    assert getattr(health, attribute) is True


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (NodeHealthState.HEALTHY, 0),
        (NodeHealthState.WARNING, 1),
        (NodeHealthState.DEGRADED, 2),
        (NodeHealthState.CRITICAL, 3),
        (NodeHealthState.UNKNOWN, None),
    ],
)
def test_node_health_severity(
    state: NodeHealthState,
    expected: int | None,
) -> None:
    assert NodeHealth(state).severity == expected


def test_node_health_worse_than() -> None:
    healthy = NodeHealth(NodeHealthState.HEALTHY)
    warning = NodeHealth(NodeHealthState.WARNING)
    degraded = NodeHealth(NodeHealthState.DEGRADED)
    critical = NodeHealth(NodeHealthState.CRITICAL)

    assert warning.worse_than(healthy) is True
    assert degraded.worse_than(warning) is True
    assert critical.worse_than(degraded) is True
    assert healthy.worse_than(critical) is False


def test_node_health_better_than() -> None:
    healthy = NodeHealth(NodeHealthState.HEALTHY)
    warning = NodeHealth(NodeHealthState.WARNING)
    degraded = NodeHealth(NodeHealthState.DEGRADED)
    critical = NodeHealth(NodeHealthState.CRITICAL)

    assert healthy.better_than(warning) is True
    assert warning.better_than(degraded) is True
    assert degraded.better_than(critical) is True
    assert critical.better_than(healthy) is False


def test_node_health_unknown_is_not_ordered() -> None:
    unknown = NodeHealth(NodeHealthState.UNKNOWN)
    healthy = NodeHealth(NodeHealthState.HEALTHY)
    critical = NodeHealth(NodeHealthState.CRITICAL)

    assert unknown.worse_than(healthy) is False
    assert unknown.better_than(critical) is False
    assert healthy.worse_than(unknown) is False
    assert critical.better_than(unknown) is False


def test_node_health_comparison_requires_node_health() -> None:
    health = NodeHealth(NodeHealthState.HEALTHY)

    with pytest.raises(TypeError):
        health.worse_than("WARNING")  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        health.better_than("WARNING")  # type: ignore[arg-type]


def test_node_health_string_representation() -> None:
    health = NodeHealth(NodeHealthState.DEGRADED)

    assert str(health) == "DEGRADED"
