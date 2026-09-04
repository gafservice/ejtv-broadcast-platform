"""Tests for canonical NOC history PDF rendering."""

from datetime import datetime, timezone

import pytest

from app.noc.domain.node_alarm import AlarmState
from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.alarm_transition import (
    AlarmTransition,
    AlarmTransitionType,
)
from app.noc.history.event_history_record import (
    EventHistoryRecord,
)
from app.noc.history.pdf_export import (
    render_history_pdf,
)


START = datetime(
    2026,
    9,
    1,
    18,
    0,
    tzinfo=timezone.utc,
)

END = datetime(
    2026,
    9,
    1,
    19,
    0,
    tzinfo=timezone.utc,
)

TIMESTAMP = datetime(
    2026,
    9,
    1,
    18,
    30,
    tzinfo=timezone.utc,
)

INSTANCE_ID = NodeInstanceId(
    "streaming-primary"
)

NODE_ID = NodeId.create(
    id="streaming-core",
    name="streaming",
    display_name="Streaming Core",
)


def make_event_record() -> EventHistoryRecord:
    return EventHistoryRecord(
        event=EventRecord(
            event_id="event-001",
            event_type="SESSION_CONNECTED",
            severity=EventSeverity.INFO,
            timestamp=TIMESTAMP,
            source=INSTANCE_ID,
            title='Reader <primary> & "connected"',
            description="SRT reader connected.\nSecond line.",
            attributes={
                "z": "last",
                "a": "first",
            },
            correlation_id="corr-001",
        ),
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        recorded_at=TIMESTAMP,
    )


def make_transition() -> AlarmTransition:
    return AlarmTransition(
        transition_id="transition-001",
        alarm_id="CRITICAL_PATH_TRAFFIC_STALLED:ejtv",
        transition_type=AlarmTransitionType.OPENED,
        timestamp=TIMESTAMP,
        source=INSTANCE_ID,
        state=AlarmState.ACTIVE,
        actor="noc-runtime",
        metadata={
            "z": "last",
            "a": "first",
        },
    )


def render_sample() -> bytes:
    return render_history_pdf(
        start=START,
        end=END,
        events=(
            make_event_record(),
        ),
        alarm_transitions=(
            make_transition(),
        ),
        node_id="streaming-core",
        instance_id="streaming-primary",
    )


def test_render_history_pdf_returns_pdf_bytes() -> None:
    document = render_sample()

    assert isinstance(
        document,
        bytes,
    )
    assert document.startswith(
        b"%PDF-"
    )
    assert document.rstrip().endswith(
        b"%%EOF"
    )
    assert len(document) > 1000


def test_empty_history_still_renders_pdf() -> None:
    document = render_history_pdf(
        start=START,
        end=END,
        events=(),
        alarm_transitions=(),
    )

    assert document.startswith(
        b"%PDF-"
    )
    assert document.rstrip().endswith(
        b"%%EOF"
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (
            "start",
            datetime(2026, 9, 1, 18, 0),
            "start must be timezone-aware and UTC",
        ),
        (
            "end",
            datetime(2026, 9, 1, 19, 0),
            "end must be timezone-aware and UTC",
        ),
    ],
)
def test_render_history_pdf_requires_utc_timestamps(
    field,
    value,
    message,
) -> None:
    arguments = {
        "start": START,
        "end": END,
        "events": (),
        "alarm_transitions": (),
    }
    arguments[field] = value

    with pytest.raises(
        ValueError,
        match=message,
    ):
        render_history_pdf(
            **arguments
        )


def test_render_history_pdf_requires_ordered_range() -> None:
    with pytest.raises(
        ValueError,
        match="start must be earlier than end",
    ):
        render_history_pdf(
            start=END,
            end=START,
            events=(),
            alarm_transitions=(),
        )


def test_render_history_pdf_requires_tuple_collections() -> None:
    with pytest.raises(
        TypeError,
        match="events must be a tuple",
    ):
        render_history_pdf(
            start=START,
            end=END,
            events=[],
            alarm_transitions=(),
        )

    with pytest.raises(
        TypeError,
        match="alarm_transitions must be a tuple",
    ):
        render_history_pdf(
            start=START,
            end=END,
            events=(),
            alarm_transitions=[],
        )


def test_render_history_pdf_rejects_invalid_domain_records() -> None:
    with pytest.raises(
        TypeError,
        match="EventHistoryRecord",
    ):
        render_history_pdf(
            start=START,
            end=END,
            events=(object(),),
            alarm_transitions=(),
        )

    with pytest.raises(
        TypeError,
        match="AlarmTransition",
    ):
        render_history_pdf(
            start=START,
            end=END,
            events=(),
            alarm_transitions=(object(),),
        )
