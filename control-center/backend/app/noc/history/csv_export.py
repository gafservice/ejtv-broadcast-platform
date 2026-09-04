"""Canonical CSV representation for durable NOC history.

ENG-013B — Operational History.

CSV is a derived representation of canonical durable history. It is not
an authority for operational state, persistence, evidence sealing,
retention, or backup.
"""

from __future__ import annotations

import csv
import io
import json

from app.noc.history.alarm_transition import AlarmTransition
from app.noc.history.event_history_record import EventHistoryRecord
from app.noc.history.evidence_writer import (
    alarm_transition_evidence_payload,
    event_evidence_payload,
)


EVENT_CSV_FIELDS = (
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

ALARM_TRANSITION_CSV_FIELDS = (
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


def _csv_value(value: object) -> str:
    """Return one deterministic textual CSV field value."""

    if value is None:
        return ""

    if isinstance(value, dict):
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    return str(value)


def event_csv_row(
    record: EventHistoryRecord,
) -> dict[str, str]:
    """Return one canonical CSV row for an historical event."""

    payload = event_evidence_payload(record)

    return {
        field: _csv_value(payload[field])
        for field in EVENT_CSV_FIELDS
    }


def alarm_transition_csv_row(
    transition: AlarmTransition,
) -> dict[str, str]:
    """Return one canonical CSV row for an alarm lifecycle transition."""

    payload = alarm_transition_evidence_payload(
        transition
    )

    return {
        field: _csv_value(payload[field])
        for field in ALARM_TRANSITION_CSV_FIELDS
    }


def _serialize_csv_rows(
    *,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, str], ...],
) -> str:
    """Serialize canonical rows as one deterministic CSV document."""

    buffer = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
        extrasaction="raise",
        lineterminator="\n",
    )

    writer.writeheader()

    for row in rows:
        writer.writerow(row)

    return buffer.getvalue()


def serialize_event_csv(
    records: tuple[EventHistoryRecord, ...],
) -> str:
    """Serialize historical events as one canonical CSV document."""

    if not isinstance(records, tuple):
        raise TypeError(
            "records must be a tuple"
        )

    rows = tuple(
        event_csv_row(record)
        for record in records
    )

    return _serialize_csv_rows(
        fieldnames=EVENT_CSV_FIELDS,
        rows=rows,
    )


def serialize_alarm_transition_csv(
    transitions: tuple[AlarmTransition, ...],
) -> str:
    """Serialize alarm transitions as one canonical CSV document."""

    if not isinstance(transitions, tuple):
        raise TypeError(
            "transitions must be a tuple"
        )

    rows = tuple(
        alarm_transition_csv_row(
            transition
        )
        for transition in transitions
    )

    return _serialize_csv_rows(
        fieldnames=ALARM_TRANSITION_CSV_FIELDS,
        rows=rows,
    )
