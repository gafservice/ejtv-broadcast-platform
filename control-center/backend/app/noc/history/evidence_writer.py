"""Ports and canonical serialization for NOC evidence files.

ENG-013B — persistent operational history.

Evidence files are append-only historical artifacts.  This module defines
the output contract independently from the filesystem implementation so
that operational persistence and evidence generation remain separate
concerns.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Protocol, runtime_checkable

from app.noc.history.alarm_transition import AlarmTransition
from app.noc.history.event_history_record import EventHistoryRecord


EVIDENCE_SCHEMA_VERSION = 1


def _utc_timestamp(value: datetime) -> str:
    """Serialize one canonical UTC timestamp."""

    return value.isoformat().replace("+00:00", "Z")


def serialize_event_evidence(
    record: EventHistoryRecord,
) -> str:
    """Serialize one EventHistoryRecord as canonical JSONL payload."""

    event = record.event

    payload = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "record_type": "event",
        "event_id": event.event_id,
        "event_type": event.event_type,
        "severity": event.severity.value,
        "timestamp": _utc_timestamp(event.timestamp),
        "source": str(event.source),
        "node_id": record.node_id.id,
        "instance_id": str(record.instance_id),
        "title": event.title,
        "description": event.description,
        "attributes": (
            dict(event.attributes)
            if event.attributes is not None
            else None
        ),
        "correlation_id": event.correlation_id,
        "recorded_at": _utc_timestamp(record.recorded_at),
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def serialize_alarm_transition_evidence(
    transition: AlarmTransition,
) -> str:
    """Serialize one AlarmTransition as canonical JSONL payload."""

    payload = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "record_type": "alarm_transition",
        "transition_id": transition.transition_id,
        "alarm_id": transition.alarm_id,
        "transition_type": transition.transition_type.value,
        "timestamp": _utc_timestamp(transition.timestamp),
        "source": str(transition.source),
        "state": transition.state.value,
        "actor": transition.actor,
        "metadata": (
            dict(transition.metadata)
            if transition.metadata is not None
            else None
        ),
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


@runtime_checkable
class EvidenceWriter(Protocol):
    """Output port for append-only operational evidence."""

    def append_event(
        self,
        record: EventHistoryRecord,
    ) -> None:
        """Append one immutable Event evidence record."""

        ...

    def append_alarm_transition(
        self,
        transition: AlarmTransition,
    ) -> None:
        """Append one immutable AlarmTransition evidence record."""

        ...
