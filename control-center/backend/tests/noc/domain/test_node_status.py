"""Tests for NodeStatus.

ENG-013B — Node SDK
NCS reference: 11-NODE-STATUS.md
"""

import pytest

from app.noc.domain.node_status import (
    NodeStatus,
    NodeStatusState,
)


def test_node_status_state_contains_canonical_values() -> None:
    expected = {
        "CREATED",
        "INITIALIZING",
        "STARTING",
        "RUNNING",
        "DEGRADED",
        "MAINTENANCE",
        "STOPPING",
        "STOPPED",
        "FAILED",
        "UNKNOWN",
    }

    assert {state.value for state in NodeStatusState} == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("CREATED", NodeStatusState.CREATED),
        ("created", NodeStatusState.CREATED),
        (" initializing ", NodeStatusState.INITIALIZING),
        ("starting", NodeStatusState.STARTING),
        ("running", NodeStatusState.RUNNING),
        ("degraded", NodeStatusState.DEGRADED),
        ("maintenance", NodeStatusState.MAINTENANCE),
        ("stopping", NodeStatusState.STOPPING),
        ("stopped", NodeStatusState.STOPPED),
        ("failed", NodeStatusState.FAILED),
        ("unknown", NodeStatusState.UNKNOWN),
    ],
)
def test_node_status_state_from_value(
    raw: str,
    expected: NodeStatusState,
) -> None:
    assert NodeStatusState.from_value(raw) is expected


def test_node_status_state_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        NodeStatusState.from_value("ONLINE")


def test_node_status_state_rejects_empty_value() -> None:
    with pytest.raises(ValueError):
        NodeStatusState.from_value("   ")


def test_node_status_state_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        NodeStatusState.from_value(123)  # type: ignore[arg-type]


def test_node_status_can_be_created() -> None:
    status = NodeStatus(NodeStatusState.RUNNING)

    assert status.state is NodeStatusState.RUNNING


def test_node_status_from_value() -> None:
    status = NodeStatus.from_value(" running ")

    assert status.state is NodeStatusState.RUNNING


def test_node_status_rejects_invalid_state_type() -> None:
    with pytest.raises(TypeError):
        NodeStatus("RUNNING")  # type: ignore[arg-type]


def test_node_status_is_immutable() -> None:
    status = NodeStatus(NodeStatusState.RUNNING)

    with pytest.raises(AttributeError):
        status.state = NodeStatusState.STOPPED  # type: ignore[misc]


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (NodeStatusState.RUNNING, True),
        (NodeStatusState.DEGRADED, True),
        (NodeStatusState.STARTING, False),
        (NodeStatusState.STOPPED, False),
        (NodeStatusState.FAILED, False),
    ],
)
def test_node_status_is_running(
    state: NodeStatusState,
    expected: bool,
) -> None:
    assert NodeStatus(state).is_running is expected


def test_node_status_is_stopped() -> None:
    assert NodeStatus(NodeStatusState.STOPPED).is_stopped is True
    assert NodeStatus(NodeStatusState.RUNNING).is_stopped is False


def test_node_status_is_failed() -> None:
    assert NodeStatus(NodeStatusState.FAILED).is_failed is True
    assert NodeStatus(NodeStatusState.RUNNING).is_failed is False


def test_node_status_is_maintenance() -> None:
    status = NodeStatus(NodeStatusState.MAINTENANCE)

    assert status.is_maintenance is True


def test_node_status_is_unknown() -> None:
    status = NodeStatus(NodeStatusState.UNKNOWN)

    assert status.is_unknown is True


def test_node_status_string_representation() -> None:
    status = NodeStatus(NodeStatusState.RUNNING)

    assert str(status) == "RUNNING"
