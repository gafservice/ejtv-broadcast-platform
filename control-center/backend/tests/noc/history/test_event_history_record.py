from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.event_history_record import (
    EventHistoryRecord,
)


EVENT_TIME = datetime(
    2026,
    9,
    1,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)

RECORDED_TIME = datetime(
    2026,
    9,
    1,
    12,
    0,
    1,
    tzinfo=timezone.utc,
)


def make_event(
    *,
    instance_id: str = "instance-001",
) -> EventRecord:
    return EventRecord(
        event_id="event-001",
        event_type="SESSION_CONNECTED",
        severity=EventSeverity.INFO,
        timestamp=EVENT_TIME,
        source=NodeInstanceId(instance_id),
        title="Session connected",
        description="SRT reader connected",
    )


def make_history(**overrides) -> EventHistoryRecord:
    values = {
        "event": make_event(),
        "node_id": NodeId(
            id="node-001",
            name="node-001",
            display_name="Node 001",
            created_at=EVENT_TIME,
        ),
        "instance_id": NodeInstanceId("instance-001"),
        "recorded_at": RECORDED_TIME,
    }
    values.update(overrides)
    return EventHistoryRecord(**values)


def test_event_history_record_is_created() -> None:
    record = make_history()

    assert record.event_id == "event-001"
    assert record.timestamp == EVENT_TIME
    assert record.node_id == NodeId(
        id="node-001",
        name="node-001",
        display_name="Node 001",
        created_at=EVENT_TIME,
    )
    assert record.instance_id == NodeInstanceId("instance-001")
    assert record.recorded_at == RECORDED_TIME


def test_event_must_be_event_record() -> None:
    with pytest.raises(TypeError):
        make_history(event="event")


def test_node_id_must_be_node_id() -> None:
    with pytest.raises(TypeError):
        make_history(node_id="node-001")


def test_instance_id_must_be_node_instance_id() -> None:
    with pytest.raises(TypeError):
        make_history(instance_id="instance-001")


def test_instance_id_must_match_event_source() -> None:
    with pytest.raises(ValueError):
        make_history(
            instance_id=NodeInstanceId("instance-002")
        )


def test_recorded_at_must_be_datetime() -> None:
    with pytest.raises(TypeError):
        make_history(
            recorded_at="2026-09-01T12:00:01Z"
        )


def test_recorded_at_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError):
        make_history(
            recorded_at=datetime(
                2026,
                9,
                1,
                12,
                0,
                1,
            )
        )


def test_recorded_at_must_be_utc() -> None:
    local_tz = timezone(timedelta(hours=-6))

    with pytest.raises(ValueError):
        make_history(
            recorded_at=datetime(
                2026,
                9,
                1,
                6,
                0,
                1,
                tzinfo=local_tz,
            )
        )
