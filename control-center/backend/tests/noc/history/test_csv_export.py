"""Tests for canonical in-memory CSV history representation."""

from __future__ import annotations

import json
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
from app.noc.history.csv_export import (
    ALARM_TRANSITION_CSV_FIELDS,
    EVENT_CSV_FIELDS,
    alarm_transition_csv_row,
    event_csv_row,
)
from app.noc.history.event_history_record import (
    EventHistoryRecord,
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


def make_event_record(
    *,
    attributes=None,
    correlation_id=None,
) -> EventHistoryRecord:
    return EventHistoryRecord(
        event=EventRecord(
            event_id="event-001",
            event_type="SESSION_CONNECTED",
            severity=EventSeverity.INFO,
            timestamp=TIMESTAMP,
            source=INSTANCE_ID,
            title="Reader connected",
            description="SRT reader connected.",
            attributes=attributes,
            correlation_id=correlation_id,
        ),
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        recorded_at=TIMESTAMP,
    )


def make_transition(
    *,
    actor=None,
    metadata=None,
) -> AlarmTransition:
    return AlarmTransition(
        transition_id="transition-001",
        alarm_id="CRITICAL_PATH_TRAFFIC_STALLED:ejtv",
        transition_type=AlarmTransitionType.OPENED,
        timestamp=TIMESTAMP,
        source=INSTANCE_ID,
        state=AlarmState.ACTIVE,
        actor=actor,
        metadata=metadata,
    )


def test_event_csv_fields_are_canonical_and_stable() -> None:
    assert EVENT_CSV_FIELDS == (
        "schema_version",
        "record_type",
        "event_id",
        "event_type",
        "severity",
        "timestamp",
        "source",
        "node_id",
        "instance_id",
        "title",
        "description",
        "attributes",
        "correlation_id",
        "recorded_at",
    )


def test_alarm_transition_csv_fields_are_canonical_and_stable() -> None:
    assert ALARM_TRANSITION_CSV_FIELDS == (
        "schema_version",
        "record_type",
        "transition_id",
        "alarm_id",
        "transition_type",
        "timestamp",
        "source",
        "state",
        "actor",
        "metadata",
    )


def test_event_csv_row_uses_canonical_payload() -> None:
    row = event_csv_row(
        make_event_record(
            attributes={
                "z": "last",
                "a": "first",
            },
            correlation_id="corr-001",
        )
    )

    assert tuple(row) == EVENT_CSV_FIELDS
    assert row["schema_version"] == "1"
    assert row["record_type"] == "event"
    assert row["event_id"] == "event-001"
    assert row["timestamp"] == "2026-09-01T18:30:00Z"
    assert row["node_id"] == "streaming-core"
    assert row["instance_id"] == "streaming-primary"
    assert row["correlation_id"] == "corr-001"

    assert json.loads(row["attributes"]) == {
        "a": "first",
        "z": "last",
    }

    assert row["attributes"] == (
        '{"a":"first","z":"last"}'
    )


def test_alarm_transition_csv_row_uses_canonical_payload() -> None:
    row = alarm_transition_csv_row(
        make_transition(
            actor="noc-runtime",
            metadata={
                "z": "last",
                "a": "first",
            },
        )
    )

    assert tuple(row) == ALARM_TRANSITION_CSV_FIELDS
    assert row["schema_version"] == "1"
    assert row["record_type"] == "alarm_transition"
    assert row["transition_id"] == "transition-001"
    assert row["alarm_id"] == (
        "CRITICAL_PATH_TRAFFIC_STALLED:ejtv"
    )
    assert row["transition_type"] == "OPENED"
    assert row["timestamp"] == "2026-09-01T18:30:00Z"
    assert row["state"] == "ACTIVE"
    assert row["actor"] == "noc-runtime"

    assert row["metadata"] == (
        '{"a":"first","z":"last"}'
    )


def test_optional_values_are_empty_csv_fields() -> None:
    event_row = event_csv_row(
        make_event_record()
    )
    transition_row = alarm_transition_csv_row(
        make_transition()
    )

    assert event_row["attributes"] == ""
    assert event_row["correlation_id"] == ""
    assert transition_row["actor"] == ""
    assert transition_row["metadata"] == ""


def test_structured_csv_fields_are_deterministic() -> None:
    first_event = event_csv_row(
        make_event_record(
            attributes={
                "z": "last",
                "a": "first",
            }
        )
    )
    second_event = event_csv_row(
        make_event_record(
            attributes={
                "a": "first",
                "z": "last",
            }
        )
    )

    first_alarm = alarm_transition_csv_row(
        make_transition(
            metadata={
                "z": "last",
                "a": "first",
            }
        )
    )
    second_alarm = alarm_transition_csv_row(
        make_transition(
            metadata={
                "a": "first",
                "z": "last",
            }
        )
    )

    assert first_event == second_event
    assert first_alarm == second_alarm


def test_csv_row_helpers_reject_invalid_domain_objects() -> None:
    with pytest.raises(
        TypeError,
        match="EventHistoryRecord",
    ):
        event_csv_row(object())

    with pytest.raises(
        TypeError,
        match="AlarmTransition",
    ):
        alarm_transition_csv_row(object())
