"""Tests for NodeType.

ENG-013B — Node SDK
NCS reference: 08-NODE-TYPE.md
"""

import pytest

from app.noc.domain.node_type import NodeType


def test_node_type_contains_canonical_values() -> None:
    expected = {
        "IDENTITY",
        "STREAMING",
        "TRANSCODING",
        "METRICS",
        "ALARM",
        "AUTOMATION",
        "STORAGE",
        "DATABASE",
        "NETWORK",
        "EDGE",
        "SYSTEM",
    }

    assert {item.value for item in NodeType} == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("IDENTITY", NodeType.IDENTITY),
        ("identity", NodeType.IDENTITY),
        (" streaming ", NodeType.STREAMING),
        ("Transcoding", NodeType.TRANSCODING),
        ("metrics", NodeType.METRICS),
        ("alarm", NodeType.ALARM),
        ("automation", NodeType.AUTOMATION),
        ("storage", NodeType.STORAGE),
        ("database", NodeType.DATABASE),
        ("network", NodeType.NETWORK),
        ("edge", NodeType.EDGE),
        ("system", NodeType.SYSTEM),
    ],
)
def test_node_type_from_value(
    raw: str,
    expected: NodeType,
) -> None:
    assert NodeType.from_value(raw) is expected


def test_node_type_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        NodeType.from_value("UNKNOWN-TYPE")


def test_node_type_rejects_empty_value() -> None:
    with pytest.raises(ValueError):
        NodeType.from_value("   ")


def test_node_type_rejects_non_string_value() -> None:
    with pytest.raises(TypeError):
        NodeType.from_value(123)  # type: ignore[arg-type]


def test_node_type_string_representation_is_canonical() -> None:
    assert str(NodeType.STREAMING) == "STREAMING"


def test_node_type_is_string_compatible() -> None:
    assert NodeType.STREAMING == "STREAMING"
