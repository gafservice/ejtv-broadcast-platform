"""Tests for JsonSerializer.

ENG-013B — Node SDK
NCS reference: 23-SERIALIZATION.md
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from types import MappingProxyType

import pytest

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_type import NodeType
from app.noc.serializers.json_serializer import JsonSerializer


class ExampleEnum(str, Enum):
    VALUE = "VALUE"


@dataclass(frozen=True)
class Example:
    name: str
    number: int


def test_serializer_supports_none() -> None:
    serializer = JsonSerializer()

    assert serializer.to_primitive(None) is None


def test_serializer_supports_scalars() -> None:
    serializer = JsonSerializer()

    assert serializer.to_primitive("text") == "text"
    assert serializer.to_primitive(10) == 10
    assert serializer.to_primitive(3.5) == 3.5
    assert serializer.to_primitive(True) is True


def test_serializer_supports_enum() -> None:
    serializer = JsonSerializer()

    assert (
        serializer.to_primitive(
            ExampleEnum.VALUE
        )
        == "VALUE"
    )


def test_serializer_supports_utc_datetime() -> None:
    serializer = JsonSerializer()

    value = datetime(
        2026,
        8,
        12,
        20,
        30,
        0,
        tzinfo=timezone.utc,
    )

    assert (
        serializer.to_primitive(value)
        == "2026-08-12T20:30:00Z"
    )


def test_serializer_preserves_microseconds() -> None:
    serializer = JsonSerializer()

    value = datetime(
        2026,
        8,
        12,
        20,
        30,
        0,
        123456,
        tzinfo=timezone.utc,
    )

    assert (
        serializer.to_primitive(value)
        == "2026-08-12T20:30:00.123456Z"
    )


def test_serializer_rejects_naive_datetime() -> None:
    serializer = JsonSerializer()

    with pytest.raises(ValueError):
        serializer.to_primitive(
            datetime(2026, 8, 12, 20, 30)
        )


def test_serializer_rejects_non_utc_datetime() -> None:
    serializer = JsonSerializer()

    non_utc = timezone(
        timedelta(hours=-6)
    )

    with pytest.raises(ValueError):
        serializer.to_primitive(
            datetime(
                2026,
                8,
                12,
                14,
                30,
                tzinfo=non_utc,
            )
        )


def test_serializer_supports_tuple() -> None:
    serializer = JsonSerializer()

    assert serializer.to_primitive(
        ("a", "b")
    ) == ["a", "b"]


def test_serializer_supports_list() -> None:
    serializer = JsonSerializer()

    assert serializer.to_primitive(
        [1, 2, 3]
    ) == [1, 2, 3]


def test_serializer_supports_mapping() -> None:
    serializer = JsonSerializer()

    assert serializer.to_primitive(
        {"cpu_usage": 42.5}
    ) == {
        "cpu_usage": 42.5,
    }


def test_serializer_supports_mapping_proxy() -> None:
    serializer = JsonSerializer()

    value = MappingProxyType(
        {"protocol": "SRT"}
    )

    assert serializer.to_primitive(
        value
    ) == {
        "protocol": "SRT",
    }


def test_serializer_supports_dataclass() -> None:
    serializer = JsonSerializer()

    value = Example(
        name="example",
        number=42,
    )

    assert serializer.to_primitive(
        value
    ) == {
        "name": "example",
        "number": 42,
    }


def test_serializer_preserves_dataclass_field_names() -> None:
    serializer = JsonSerializer()

    node_id = NodeId.create(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
    )

    result = serializer.to_primitive(
        node_id
    )

    assert set(result) == {
        "id",
        "name",
        "display_name",
        "created_at",
    }


def test_serializer_serializes_enum_domain_value() -> None:
    serializer = JsonSerializer()

    assert serializer.to_primitive(
        NodeType.STREAMING
    ) == "STREAMING"


def test_serializer_dumps_valid_json() -> None:
    serializer = JsonSerializer()

    encoded = serializer.dumps(
        {
            "node_type": NodeType.STREAMING,
            "value": 42,
        }
    )

    decoded = json.loads(encoded)

    assert decoded == {
        "node_type": "STREAMING",
        "value": 42,
    }


def test_serializer_output_is_deterministic() -> None:
    serializer = JsonSerializer()

    first = serializer.dumps(
        {
            "z": 1,
            "a": 2,
        }
    )

    second = serializer.dumps(
        {
            "a": 2,
            "z": 1,
        }
    )

    assert first == second


def test_serializer_compact_output() -> None:
    serializer = JsonSerializer()

    assert serializer.dumps(
        {"b": 2, "a": 1}
    ) == '{"a":1,"b":2}'


def test_serializer_pretty_output() -> None:
    serializer = JsonSerializer()

    encoded = serializer.dumps(
        {
            "node_type": NodeType.STREAMING,
        },
        indent=2,
    )

    assert "\n" in encoded

    assert json.loads(encoded) == {
        "node_type": "STREAMING",
    }


def test_serializer_rejects_unknown_type() -> None:
    serializer = JsonSerializer()

    with pytest.raises(TypeError):
        serializer.to_primitive(
            object()
        )
