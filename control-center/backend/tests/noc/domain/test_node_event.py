"""Tests for NodeEvent.

ENG-013B — Node SDK
NCS reference: 17-NODE-EVENT.md
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
    NodeEvent,
)
from app.noc.domain.node_instance import NodeInstanceId


def make_event(
    *,
    event_id: str = "evt-001",
    event_type: str = "INSTANCE_STARTED",
    severity: EventSeverity = EventSeverity.INFO,
    correlation_id: str | None = None,
) -> EventRecord:
    return EventRecord(
        event_id=event_id,
        event_type=event_type,
        severity=severity,
        timestamp=datetime.now(timezone.utc),
        source=NodeInstanceId("streaming-primary"),
        title="Streaming service started",
        description="The streaming service entered normal operation.",
        attributes={
            "protocol": "SRT",
        },
        correlation_id=correlation_id,
    )


def test_event_severity_contains_canonical_values() -> None:
    expected = {
        "INFO",
        "NOTICE",
        "WARNING",
        "ERROR",
        "CRITICAL",
    }

    assert {
        severity.value for severity in EventSeverity
    } == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("info", EventSeverity.INFO),
        (" NOTICE ", EventSeverity.NOTICE),
        ("warning", EventSeverity.WARNING),
        ("error", EventSeverity.ERROR),
        ("critical", EventSeverity.CRITICAL),
    ],
)
def test_event_severity_from_value(
    raw: str,
    expected: EventSeverity,
) -> None:
    assert EventSeverity.from_value(raw) is expected


def test_event_severity_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        EventSeverity.from_value("DEBUG")


def test_event_severity_rejects_empty_value() -> None:
    with pytest.raises(ValueError):
        EventSeverity.from_value("   ")


def test_event_record_can_be_created() -> None:
    event = make_event()

    assert event.event_id == "evt-001"
    assert event.event_type == "INSTANCE_STARTED"
    assert event.severity is EventSeverity.INFO
    assert event.source == NodeInstanceId("streaming-primary")


def test_event_record_normalizes_strings() -> None:
    event = EventRecord(
        event_id="  evt-001  ",
        event_type="  instance_started  ",
        severity=EventSeverity.INFO,
        timestamp=datetime.now(timezone.utc),
        source=NodeInstanceId("streaming-primary"),
        title="  Started  ",
        description="  Service started correctly.  ",
    )

    assert event.event_id == "evt-001"
    assert event.event_type == "INSTANCE_STARTED"
    assert event.title == "Started"
    assert event.description == "Service started correctly."


@pytest.mark.parametrize(
    "field",
    [
        "event_id",
        "event_type",
        "title",
        "description",
    ],
)
def test_event_record_rejects_empty_required_strings(
    field: str,
) -> None:
    values = {
        "event_id": "evt-001",
        "event_type": "INSTANCE_STARTED",
        "severity": EventSeverity.INFO,
        "timestamp": datetime.now(timezone.utc),
        "source": NodeInstanceId("streaming-primary"),
        "title": "Started",
        "description": "Service started.",
    }

    values[field] = "   "

    with pytest.raises(ValueError):
        EventRecord(**values)


def test_event_record_rejects_invalid_severity_type() -> None:
    with pytest.raises(TypeError):
        EventRecord(
            event_id="evt-001",
            event_type="INSTANCE_STARTED",
            severity="INFO",  # type: ignore[arg-type]
            timestamp=datetime.now(timezone.utc),
            source=NodeInstanceId("streaming-primary"),
            title="Started",
            description="Service started.",
        )


def test_event_record_rejects_invalid_source_type() -> None:
    with pytest.raises(TypeError):
        EventRecord(
            event_id="evt-001",
            event_type="INSTANCE_STARTED",
            severity=EventSeverity.INFO,
            timestamp=datetime.now(timezone.utc),
            source="streaming-primary",  # type: ignore[arg-type]
            title="Started",
            description="Service started.",
        )


def test_event_record_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError):
        EventRecord(
            event_id="evt-001",
            event_type="INSTANCE_STARTED",
            severity=EventSeverity.INFO,
            timestamp=datetime(2026, 8, 11, 18, 0),
            source=NodeInstanceId("streaming-primary"),
            title="Started",
            description="Service started.",
        )


def test_event_record_rejects_non_utc_timestamp() -> None:
    non_utc = timezone(timedelta(hours=-6))

    with pytest.raises(ValueError):
        EventRecord(
            event_id="evt-001",
            event_type="INSTANCE_STARTED",
            severity=EventSeverity.INFO,
            timestamp=datetime(
                2026,
                8,
                11,
                12,
                0,
                tzinfo=non_utc,
            ),
            source=NodeInstanceId("streaming-primary"),
            title="Started",
            description="Service started.",
        )


def test_event_record_attributes_are_normalized() -> None:
    event = EventRecord(
        event_id="evt-001",
        event_type="INSTANCE_STARTED",
        severity=EventSeverity.INFO,
        timestamp=datetime.now(timezone.utc),
        source=NodeInstanceId("streaming-primary"),
        title="Started",
        description="Service started.",
        attributes={
            " protocol ": " SRT ",
        },
    )

    assert event.attributes == {
        "protocol": "SRT",
    }


def test_event_record_attributes_are_immutable() -> None:
    event = make_event()

    with pytest.raises(TypeError):
        event.attributes["protocol"] = "RTMP"  # type: ignore[index]


def test_event_record_correlation_id_normalizes() -> None:
    event = make_event(
        correlation_id="  operation-001  "
    )

    assert event.correlation_id == "operation-001"


def test_event_record_empty_correlation_becomes_none() -> None:
    event = make_event(
        correlation_id="   "
    )

    assert event.correlation_id is None


def test_event_record_is_immutable() -> None:
    event = make_event()

    with pytest.raises(AttributeError):
        event.title = "Changed"  # type: ignore[misc]


def test_event_record_severity_flags() -> None:
    assert make_event(
        severity=EventSeverity.CRITICAL
    ).is_critical is True

    assert make_event(
        severity=EventSeverity.ERROR
    ).is_error is True

    assert make_event(
        severity=EventSeverity.WARNING
    ).is_warning is True

    assert make_event(
        severity=EventSeverity.INFO
    ).is_informational is True

    assert make_event(
        severity=EventSeverity.NOTICE
    ).is_informational is True


def test_event_record_string_representation() -> None:
    event = make_event()

    assert str(event) == (
        "INSTANCE_STARTED: Streaming service started"
    )


def test_node_event_can_be_empty() -> None:
    events = NodeEvent()

    assert events.events == ()
    assert len(events) == 0


def test_node_event_accepts_multiple_events() -> None:
    events = NodeEvent(
        events=(
            make_event(event_id="evt-001"),
            make_event(
                event_id="evt-002",
                event_type="STREAM_CREATED",
            ),
        )
    )

    assert len(events) == 2


def test_node_event_rejects_duplicate_event_ids() -> None:
    with pytest.raises(ValueError):
        NodeEvent(
            events=(
                make_event(event_id="evt-001"),
                make_event(event_id="evt-001"),
            )
        )


def test_node_event_get_event() -> None:
    event = make_event()

    events = NodeEvent(events=(event,))

    assert events.get("evt-001") is event


def test_node_event_get_unknown_returns_none() -> None:
    events = NodeEvent()

    assert events.get("evt-missing") is None


def test_node_event_by_type() -> None:
    events = NodeEvent(
        events=(
            make_event(
                event_id="evt-001",
                event_type="INSTANCE_STARTED",
            ),
            make_event(
                event_id="evt-002",
                event_type="STREAM_CREATED",
            ),
            make_event(
                event_id="evt-003",
                event_type="STREAM_CREATED",
            ),
        )
    )

    result = events.by_type("stream_created")

    assert len(result) == 2


def test_node_event_by_severity() -> None:
    events = NodeEvent(
        events=(
            make_event(
                event_id="evt-001",
                severity=EventSeverity.INFO,
            ),
            make_event(
                event_id="evt-002",
                severity=EventSeverity.CRITICAL,
            ),
        )
    )

    result = events.by_severity(
        EventSeverity.CRITICAL
    )

    assert len(result) == 1
    assert result[0].event_id == "evt-002"


def test_node_event_by_correlation() -> None:
    events = NodeEvent(
        events=(
            make_event(
                event_id="evt-001",
                correlation_id="op-001",
            ),
            make_event(
                event_id="evt-002",
                correlation_id="op-001",
            ),
            make_event(
                event_id="evt-003",
                correlation_id="op-002",
            ),
        )
    )

    result = events.by_correlation("op-001")

    assert len(result) == 2


def test_node_event_rejects_non_tuple_events() -> None:
    with pytest.raises(TypeError):
        NodeEvent(
            events=[]  # type: ignore[arg-type]
        )


def test_node_event_rejects_invalid_entry() -> None:
    with pytest.raises(TypeError):
        NodeEvent(
            events=(
                "INSTANCE_STARTED",  # type: ignore[arg-type]
            )
        )
