"""Tests for NodeId.

ENG-013B — Node SDK
NCS reference: 07-NODE-ID.md
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node_id import NodeId


def test_node_id_can_be_created() -> None:
    created_at = datetime(2026, 8, 11, 18, 0, tzinfo=timezone.utc)

    node_id = NodeId(
        id="550e8400-e29b-41d4-a716-446655440000",
        name="streaming",
        display_name="Primary Streaming Service",
        created_at=created_at,
    )

    assert node_id.id == "550e8400-e29b-41d4-a716-446655440000"
    assert node_id.name == "streaming"
    assert node_id.display_name == "Primary Streaming Service"
    assert node_id.created_at == created_at


def test_node_id_create_uses_utc_time() -> None:
    node_id = NodeId.create(
        id="node-001",
        name="identity",
        display_name="Identity Service",
    )

    assert node_id.created_at.tzinfo is not None
    assert node_id.created_at.utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", ""),
        ("name", ""),
        ("display_name", ""),
        ("id", "   "),
        ("name", "   "),
        ("display_name", "   "),
    ],
)
def test_node_id_rejects_empty_required_strings(
    field: str,
    value: str,
) -> None:
    values = {
        "id": "node-001",
        "name": "streaming",
        "display_name": "Streaming Service",
        "created_at": datetime.now(timezone.utc),
    }
    values[field] = value

    with pytest.raises(ValueError):
        NodeId(**values)


def test_node_id_normalizes_surrounding_whitespace() -> None:
    node_id = NodeId(
        id="  node-001  ",
        name="  streaming  ",
        display_name="  Streaming Service  ",
        created_at=datetime.now(timezone.utc),
    )

    assert node_id.id == "node-001"
    assert node_id.name == "streaming"
    assert node_id.display_name == "Streaming Service"


def test_node_id_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError):
        NodeId(
            id="node-001",
            name="streaming",
            display_name="Streaming Service",
            created_at=datetime(2026, 8, 11, 18, 0),
        )


def test_node_id_rejects_non_utc_datetime() -> None:
    non_utc = timezone(timedelta(hours=-6))

    with pytest.raises(ValueError):
        NodeId(
            id="node-001",
            name="streaming",
            display_name="Streaming Service",
            created_at=datetime(2026, 8, 11, 12, 0, tzinfo=non_utc),
        )


def test_node_id_is_immutable() -> None:
    node_id = NodeId.create(
        id="node-001",
        name="streaming",
        display_name="Streaming Service",
    )

    with pytest.raises(AttributeError):
        node_id.id = "node-002"  # type: ignore[misc]


def test_node_id_string_representation_is_canonical_id() -> None:
    node_id = NodeId.create(
        id="node-001",
        name="streaming",
        display_name="Streaming Service",
    )

    assert str(node_id) == "node-001"


def test_node_id_accepts_non_uuid_identifier() -> None:
    node_id = NodeId.create(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
    )

    assert node_id.id == "streaming-core"
