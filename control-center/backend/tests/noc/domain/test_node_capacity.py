"""Tests for NodeCapacity.

ENG-013B — Node SDK
NCS reference: 15-NODE-CAPACITY.md
"""

import math

import pytest

from app.noc.domain.node_capacity import (
    CapacityResource,
    NodeCapacity,
)


def make_stream_capacity() -> CapacityResource:
    return CapacityResource(
        resource="Streaming Channels",
        maximum=16,
        allocated=10,
        reserved=2,
        available=4,
        unit="channels",
    )


def test_capacity_resource_can_be_created() -> None:
    resource = make_stream_capacity()

    assert resource.resource == "Streaming Channels"
    assert resource.maximum == 16
    assert resource.allocated == 10
    assert resource.reserved == 2
    assert resource.available == 4
    assert resource.unit == "channels"


def test_capacity_resource_normalizes_strings() -> None:
    resource = CapacityResource(
        resource="  Network Bandwidth  ",
        maximum=1000,
        allocated=500,
        reserved=100,
        available=400,
        unit="  Mbps  ",
    )

    assert resource.resource == "Network Bandwidth"
    assert resource.unit == "Mbps"


@pytest.mark.parametrize(
    "field",
    ["resource", "unit"],
)
def test_capacity_resource_rejects_empty_strings(
    field: str,
) -> None:
    values = {
        "resource": "Streaming Channels",
        "maximum": 16,
        "allocated": 10,
        "reserved": 2,
        "available": 4,
        "unit": "channels",
    }

    values[field] = "   "

    with pytest.raises(ValueError):
        CapacityResource(**values)


@pytest.mark.parametrize(
    "field",
    [
        "maximum",
        "allocated",
        "reserved",
        "available",
    ],
)
def test_capacity_resource_rejects_negative_values(
    field: str,
) -> None:
    values = {
        "resource": "Streaming Channels",
        "maximum": 16,
        "allocated": 10,
        "reserved": 2,
        "available": 4,
        "unit": "channels",
    }

    values[field] = -1

    with pytest.raises(ValueError):
        CapacityResource(**values)


@pytest.mark.parametrize(
    "value",
    [
        float("inf"),
        float("-inf"),
        float("nan"),
    ],
)
def test_capacity_resource_rejects_non_finite_values(
    value: float,
) -> None:
    with pytest.raises(ValueError):
        CapacityResource(
            resource="Bandwidth",
            maximum=value,
            allocated=0,
            reserved=0,
            available=0,
            unit="Mbps",
        )


def test_capacity_resource_rejects_boolean_numeric_value() -> None:
    with pytest.raises(TypeError):
        CapacityResource(
            resource="Streaming Channels",
            maximum=True,
            allocated=0,
            reserved=0,
            available=0,
            unit="channels",
        )


def test_capacity_resource_rejects_overcommitted_capacity() -> None:
    with pytest.raises(ValueError):
        CapacityResource(
            resource="Streaming Channels",
            maximum=16,
            allocated=12,
            reserved=2,
            available=4,
            unit="channels",
        )


def test_capacity_resource_allows_unrepresented_headroom() -> None:
    resource = CapacityResource(
        resource="Streaming Channels",
        maximum=16,
        allocated=8,
        reserved=2,
        available=4,
        unit="channels",
    )

    assert (
        resource.allocated
        + resource.reserved
        + resource.available
    ) < resource.maximum


def test_capacity_resource_committed() -> None:
    resource = make_stream_capacity()

    assert resource.committed == 12


def test_capacity_resource_utilization() -> None:
    resource = make_stream_capacity()

    assert resource.utilization == pytest.approx(
        10 / 16
    )


def test_capacity_resource_utilization_percent() -> None:
    resource = make_stream_capacity()

    assert resource.utilization_percent == pytest.approx(
        62.5
    )


def test_zero_maximum_has_zero_utilization() -> None:
    resource = CapacityResource(
        resource="GPU Jobs",
        maximum=0,
        allocated=0,
        reserved=0,
        available=0,
        unit="jobs",
    )

    assert resource.utilization == 0.0


def test_capacity_resource_reports_available_capacity() -> None:
    assert make_stream_capacity().has_available_capacity is True


def test_capacity_resource_reports_no_available_capacity() -> None:
    resource = CapacityResource(
        resource="Streaming Channels",
        maximum=16,
        allocated=14,
        reserved=2,
        available=0,
        unit="channels",
    )

    assert resource.has_available_capacity is False


def test_capacity_resource_is_immutable() -> None:
    resource = make_stream_capacity()

    with pytest.raises(AttributeError):
        resource.available = 0  # type: ignore[misc]


def test_node_capacity_can_be_empty() -> None:
    capacity = NodeCapacity()

    assert capacity.resources == ()
    assert len(capacity) == 0


def test_node_capacity_accepts_multiple_resources() -> None:
    capacity = NodeCapacity(
        resources=(
            make_stream_capacity(),
            CapacityResource(
                resource="Network Bandwidth",
                maximum=1000,
                allocated=500,
                reserved=100,
                available=400,
                unit="Mbps",
            ),
        )
    )

    assert len(capacity) == 2


def test_node_capacity_rejects_duplicate_resources() -> None:
    with pytest.raises(ValueError):
        NodeCapacity(
            resources=(
                make_stream_capacity(),
                CapacityResource(
                    resource="streaming channels",
                    maximum=16,
                    allocated=8,
                    reserved=4,
                    available=4,
                    unit="channels",
                ),
            )
        )


def test_node_capacity_get_resource() -> None:
    resource = make_stream_capacity()

    capacity = NodeCapacity(
        resources=(resource,)
    )

    assert (
        capacity.get("streaming channels")
        is resource
    )


def test_node_capacity_get_unknown_returns_none() -> None:
    capacity = NodeCapacity()

    assert capacity.get("GPU Jobs") is None


def test_node_capacity_has_resource() -> None:
    capacity = NodeCapacity(
        resources=(make_stream_capacity(),)
    )

    assert capacity.has_resource(
        "Streaming Channels"
    ) is True

    assert capacity.has_resource(
        "GPU Jobs"
    ) is False


def test_node_capacity_available_for_resource() -> None:
    capacity = NodeCapacity(
        resources=(make_stream_capacity(),)
    )

    assert capacity.available_for(
        "Streaming Channels"
    ) == 4


def test_node_capacity_available_for_unknown_returns_none() -> None:
    capacity = NodeCapacity()

    assert capacity.available_for(
        "GPU Jobs"
    ) is None


def test_node_capacity_contains_resource() -> None:
    capacity = NodeCapacity(
        resources=(make_stream_capacity(),)
    )

    assert "Streaming Channels" in capacity
    assert "streaming channels" in capacity
    assert "GPU Jobs" not in capacity


def test_node_capacity_rejects_non_tuple_resources() -> None:
    with pytest.raises(TypeError):
        NodeCapacity(
            resources=[]  # type: ignore[arg-type]
        )


def test_node_capacity_rejects_invalid_entry() -> None:
    with pytest.raises(TypeError):
        NodeCapacity(
            resources=(
                "Streaming Channels",  # type: ignore[arg-type]
            )
        )


def test_capacity_resource_string_representation() -> None:
    resource = make_stream_capacity()

    assert str(resource) == "Streaming Channels"
