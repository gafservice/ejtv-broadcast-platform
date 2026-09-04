"""Tests for canonical in-memory CSV history representation."""

from __future__ import annotations

import csv
import io
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
    serialize_alarm_transition_csv,
    serialize_event_csv,
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


def test_event_csv_document_includes_header_and_row() -> None:
    encoded = serialize_event_csv(
        (
            make_event_record(
                attributes={
                    "path": "ejtv",
                },
                correlation_id="corr-001",
            ),
        )
    )

    lines = encoded.splitlines()

    assert lines[0] == ",".join(
        EVENT_CSV_FIELDS
    )
    assert len(lines) == 2


def test_alarm_csv_document_includes_header_and_row() -> None:
    encoded = serialize_alarm_transition_csv(
        (
            make_transition(
                actor="noc-runtime",
                metadata={
                    "path": "ejtv",
                },
            ),
        )
    )

    lines = encoded.splitlines()

    assert lines[0] == ",".join(
        ALARM_TRANSITION_CSV_FIELDS
    )
    assert len(lines) == 2


def test_event_csv_document_escapes_special_characters() -> None:
    record = EventHistoryRecord(
        event=EventRecord(
            event_id="event-special",
            event_type="SESSION_CONNECTED",
            severity=EventSeverity.INFO,
            timestamp=TIMESTAMP,
            source=INSTANCE_ID,
            title='Reader "primary", connected',
            description="Line one\nLine two",
            attributes={
                "note": 'value, "quoted"',
            },
        ),
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        recorded_at=TIMESTAMP,
    )

    encoded = serialize_event_csv(
        (record,)
    )

    parsed = list(
        csv.DictReader(
            io.StringIO(encoded)
        )
    )

    assert len(parsed) == 1
    assert parsed[0]["title"] == (
        'Reader "primary", connected'
    )
    assert parsed[0]["description"] == (
        "Line one\nLine two"
    )
    assert json.loads(
        parsed[0]["attributes"]
    ) == {
        "note": 'value, "quoted"',
    }


def test_empty_csv_documents_still_include_headers() -> None:
    events = serialize_event_csv(())
    alarms = serialize_alarm_transition_csv(())

    assert events == (
        ",".join(EVENT_CSV_FIELDS) + "\n"
    )
    assert alarms == (
        ",".join(ALARM_TRANSITION_CSV_FIELDS) + "\n"
    )


def test_csv_documents_are_deterministic() -> None:
    records = (
        make_event_record(
            attributes={
                "z": "last",
                "a": "first",
            }
        ),
    )

    transitions = (
        make_transition(
            metadata={
                "z": "last",
                "a": "first",
            }
        ),
    )

    assert serialize_event_csv(
        records
    ) == serialize_event_csv(
        records
    )

    assert serialize_alarm_transition_csv(
        transitions
    ) == serialize_alarm_transition_csv(
        transitions
    )


def test_csv_document_serializers_require_tuples() -> None:
    with pytest.raises(
        TypeError,
        match="tuple",
    ):
        serialize_event_csv([])

    with pytest.raises(
        TypeError,
        match="tuple",
    ):
        serialize_alarm_transition_csv([])
