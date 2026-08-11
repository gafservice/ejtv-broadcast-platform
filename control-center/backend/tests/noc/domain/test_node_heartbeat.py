"""Tests for NodeHeartbeat.

ENG-013B — Node SDK
NCS reference: 19-NODE-HEARTBEAT.md
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node_heartbeat import (
    HeartbeatRecord,
    NodeHeartbeat,
)
from app.noc.domain.node_instance import NodeInstanceId


def make_heartbeat(
    *,
    sequence: int = 1,
) -> HeartbeatRecord:
    return HeartbeatRecord(
        heartbeat_id=f"hb-{sequence}",
        instance_id=NodeInstanceId("streaming-primary"),
        sequence=sequence,
        timestamp=datetime.now(timezone.utc),
        contract_version="1.0.0",
        uptime=120.5,
        checksum="abc123",
    )


def test_heartbeat_record_can_be_created() -> None:
    heartbeat = make_heartbeat()

    assert heartbeat.heartbeat_id == "hb-1"
    assert heartbeat.sequence == 1
    assert heartbeat.contract_version == "1.0.0"
    assert heartbeat.uptime == 120.5


def test_heartbeat_record_normalizes_strings() -> None:
    heartbeat = HeartbeatRecord(
        heartbeat_id="  hb-1  ",
        instance_id=NodeInstanceId("streaming-primary"),
        sequence=1,
        timestamp=datetime.now(timezone.utc),
        contract_version="  1.0.0  ",
        uptime=10,
        checksum="  abc123  ",
    )

    assert heartbeat.heartbeat_id == "hb-1"
    assert heartbeat.contract_version == "1.0.0"
    assert heartbeat.checksum == "abc123"


@pytest.mark.parametrize(
    "field",
    ["heartbeat_id", "contract_version"],
)
def test_heartbeat_record_rejects_empty_required_strings(
    field: str,
) -> None:
    values = {
        "heartbeat_id": "hb-1",
        "instance_id": NodeInstanceId("streaming-primary"),
        "sequence": 1,
        "timestamp": datetime.now(timezone.utc),
        "contract_version": "1.0.0",
        "uptime": 10.0,
    }

    values[field] = "   "

    with pytest.raises(ValueError):
        HeartbeatRecord(**values)


def test_heartbeat_record_rejects_invalid_instance_id() -> None:
    with pytest.raises(TypeError):
        HeartbeatRecord(
            heartbeat_id="hb-1",
            instance_id="streaming-primary",  # type: ignore[arg-type]
            sequence=1,
            timestamp=datetime.now(timezone.utc),
            contract_version="1.0.0",
            uptime=10,
        )


def test_heartbeat_record_rejects_negative_sequence() -> None:
    with pytest.raises(ValueError):
        HeartbeatRecord(
            heartbeat_id="hb-1",
            instance_id=NodeInstanceId("streaming-primary"),
            sequence=-1,
            timestamp=datetime.now(timezone.utc),
            contract_version="1.0.0",
            uptime=10,
        )


def test_heartbeat_record_rejects_boolean_sequence() -> None:
    with pytest.raises(TypeError):
        HeartbeatRecord(
            heartbeat_id="hb-1",
            instance_id=NodeInstanceId("streaming-primary"),
            sequence=True,
            timestamp=datetime.now(timezone.utc),
            contract_version="1.0.0",
            uptime=10,
        )


def test_heartbeat_record_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError):
        HeartbeatRecord(
            heartbeat_id="hb-1",
            instance_id=NodeInstanceId("streaming-primary"),
            sequence=1,
            timestamp=datetime(2026, 8, 11, 18, 0),
            contract_version="1.0.0",
            uptime=10,
        )


def test_heartbeat_record_rejects_non_utc_timestamp() -> None:
    non_utc = timezone(timedelta(hours=-6))

    with pytest.raises(ValueError):
        HeartbeatRecord(
            heartbeat_id="hb-1",
            instance_id=NodeInstanceId("streaming-primary"),
            sequence=1,
            timestamp=datetime(
                2026,
                8,
                11,
                12,
                0,
                tzinfo=non_utc,
            ),
            contract_version="1.0.0",
            uptime=10,
        )


def test_heartbeat_record_rejects_negative_uptime() -> None:
    with pytest.raises(ValueError):
        HeartbeatRecord(
            heartbeat_id="hb-1",
            instance_id=NodeInstanceId("streaming-primary"),
            sequence=1,
            timestamp=datetime.now(timezone.utc),
            contract_version="1.0.0",
            uptime=-1,
        )


def test_heartbeat_record_empty_checksum_becomes_none() -> None:
    heartbeat = HeartbeatRecord(
        heartbeat_id="hb-1",
        instance_id=NodeInstanceId("streaming-primary"),
        sequence=1,
        timestamp=datetime.now(timezone.utc),
        contract_version="1.0.0",
        uptime=10,
        checksum="   ",
    )

    assert heartbeat.checksum is None


def test_heartbeat_record_is_immutable() -> None:
    heartbeat = make_heartbeat()

    with pytest.raises(AttributeError):
        heartbeat.sequence = 2  # type: ignore[misc]


def test_heartbeat_record_string_representation() -> None:
    heartbeat = make_heartbeat()

    assert str(heartbeat) == (
        "streaming-primary seq=1"
    )


def test_node_heartbeat_can_be_empty() -> None:
    heartbeat = NodeHeartbeat()

    assert heartbeat.latest is None
    assert heartbeat.is_present is False
    assert heartbeat.sequence is None
    assert heartbeat.timestamp is None
    assert heartbeat.uptime is None


def test_node_heartbeat_accepts_latest_record() -> None:
    record = make_heartbeat()

    heartbeat = NodeHeartbeat(
        latest=record
    )

    assert heartbeat.latest is record
    assert heartbeat.is_present is True


def test_node_heartbeat_exposes_latest_sequence() -> None:
    heartbeat = NodeHeartbeat(
        latest=make_heartbeat(sequence=42)
    )

    assert heartbeat.sequence == 42


def test_node_heartbeat_exposes_latest_timestamp() -> None:
    record = make_heartbeat()

    heartbeat = NodeHeartbeat(
        latest=record
    )

    assert heartbeat.timestamp == record.timestamp


def test_node_heartbeat_exposes_latest_uptime() -> None:
    heartbeat = NodeHeartbeat(
        latest=make_heartbeat()
    )

    assert heartbeat.uptime == 120.5


def test_node_heartbeat_belongs_to_instance() -> None:
    heartbeat = NodeHeartbeat(
        latest=make_heartbeat()
    )

    assert heartbeat.belongs_to(
        NodeInstanceId("streaming-primary")
    ) is True


def test_node_heartbeat_does_not_belong_to_other_instance() -> None:
    heartbeat = NodeHeartbeat(
        latest=make_heartbeat()
    )

    assert heartbeat.belongs_to(
        NodeInstanceId("streaming-backup")
    ) is False


def test_node_heartbeat_empty_does_not_belong_to_instance() -> None:
    heartbeat = NodeHeartbeat()

    assert heartbeat.belongs_to(
        NodeInstanceId("streaming-primary")
    ) is False


def test_node_heartbeat_rejects_invalid_latest() -> None:
    with pytest.raises(TypeError):
        NodeHeartbeat(
            latest="hb-1"  # type: ignore[arg-type]
        )
