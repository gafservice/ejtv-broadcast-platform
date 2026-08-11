"""Tests for NodeAvailability.

ENG-013B — Node SDK
NCS reference: 13-NODE-AVAILABILITY.md
"""

import pytest

from app.noc.domain.node_availability import (
    NodeAvailability,
    NodeAvailabilityState,
)


def test_node_availability_contains_canonical_values() -> None:
    expected = {
        "AVAILABLE",
        "LIMITED",
        "DRAINING",
        "UNAVAILABLE",
        "UNKNOWN",
    }

    assert {
        state.value for state in NodeAvailabilityState
    } == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("AVAILABLE", NodeAvailabilityState.AVAILABLE),
        ("available", NodeAvailabilityState.AVAILABLE),
        (" limited ", NodeAvailabilityState.LIMITED),
        ("draining", NodeAvailabilityState.DRAINING),
        ("unavailable", NodeAvailabilityState.UNAVAILABLE),
        ("unknown", NodeAvailabilityState.UNKNOWN),
    ],
)
def test_node_availability_from_value(
    raw: str,
    expected: NodeAvailabilityState,
) -> None:
    assert NodeAvailabilityState.from_value(raw) is expected


def test_node_availability_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        NodeAvailabilityState.from_value("BUSY")


def test_node_availability_rejects_empty_value() -> None:
    with pytest.raises(ValueError):
        NodeAvailabilityState.from_value("   ")


def test_node_availability_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        NodeAvailabilityState.from_value(123)  # type: ignore[arg-type]


def test_node_availability_can_be_created() -> None:
    availability = NodeAvailability(
        NodeAvailabilityState.AVAILABLE
    )

    assert (
        availability.state
        is NodeAvailabilityState.AVAILABLE
    )


def test_node_availability_from_string() -> None:
    availability = NodeAvailability.from_value(
        " draining "
    )

    assert (
        availability.state
        is NodeAvailabilityState.DRAINING
    )


def test_node_availability_rejects_invalid_state_type() -> None:
    with pytest.raises(TypeError):
        NodeAvailability(
            "AVAILABLE"  # type: ignore[arg-type]
        )


def test_node_availability_is_immutable() -> None:
    availability = NodeAvailability(
        NodeAvailabilityState.AVAILABLE
    )

    with pytest.raises(AttributeError):
        availability.state = (  # type: ignore[misc]
            NodeAvailabilityState.UNAVAILABLE
        )


@pytest.mark.parametrize(
    ("state", "attribute"),
    [
        (
            NodeAvailabilityState.AVAILABLE,
            "is_available",
        ),
        (
            NodeAvailabilityState.LIMITED,
            "is_limited",
        ),
        (
            NodeAvailabilityState.DRAINING,
            "is_draining",
        ),
        (
            NodeAvailabilityState.UNAVAILABLE,
            "is_unavailable",
        ),
        (
            NodeAvailabilityState.UNKNOWN,
            "is_unknown",
        ),
    ],
)
def test_node_availability_state_flags(
    state: NodeAvailabilityState,
    attribute: str,
) -> None:
    availability = NodeAvailability(state)

    assert getattr(availability, attribute) is True


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (NodeAvailabilityState.AVAILABLE, True),
        (NodeAvailabilityState.LIMITED, True),
        (NodeAvailabilityState.DRAINING, False),
        (NodeAvailabilityState.UNAVAILABLE, False),
        (NodeAvailabilityState.UNKNOWN, False),
    ],
)
def test_accepts_new_work(
    state: NodeAvailabilityState,
    expected: bool,
) -> None:
    availability = NodeAvailability(state)

    assert availability.accepts_new_work is expected


def test_node_availability_string_representation() -> None:
    availability = NodeAvailability(
        NodeAvailabilityState.LIMITED
    )

    assert str(availability) == "LIMITED"
