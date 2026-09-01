"""Tests for filesystem JSONL operational evidence."""

from __future__ import annotations

import json
from datetime import datetime, timezone

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
from app.noc.history.jsonl_evidence_writer import (
    JsonlEvidenceWriter,
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
    event_id: str,
    timestamp: datetime,
) -> EventHistoryRecord:
    event = EventRecord(
        event_id=event_id,
        event_type="SESSION_CONNECTED",
        severity=EventSeverity.INFO,
        timestamp=timestamp,
        source=INSTANCE_ID,
        title="Connected",
        description="Reader connected.",
        attributes={
            "path": "ejtv",
        },
    )

    return EventHistoryRecord(
        event=event,
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        recorded_at=timestamp,
    )


def make_transition(
    *,
    transition_id: str,
    timestamp: datetime,
) -> AlarmTransition:
    return AlarmTransition(
        transition_id=transition_id,
        alarm_id="CRITICAL_PATH_TRAFFIC_STALLED:ejtv",
        transition_type=AlarmTransitionType.OPENED,
        timestamp=timestamp,
        source=INSTANCE_ID,
        state=AlarmState.ACTIVE,
        actor="noc-runtime",
        metadata={
            "path": "ejtv",
        },
    )


def test_append_event_creates_utc_daily_file(
    tmp_path,
) -> None:
    writer = JsonlEvidenceWriter(tmp_path)

    timestamp = datetime(
        2026,
        9,
        1,
        23,
        58,
        tzinfo=timezone.utc,
    )

    writer.append_event(
        make_event_record(
            event_id="event-001",
            timestamp=timestamp,
        )
    )

    path = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "events.jsonl"
    )

    assert path.exists()

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    payload = json.loads(lines[0])

    assert payload["event_id"] == "event-001"
    assert payload["record_type"] == "event"


def test_append_alarm_transition_creates_daily_file(
    tmp_path,
) -> None:
    writer = JsonlEvidenceWriter(tmp_path)

    timestamp = datetime(
        2026,
        9,
        1,
        23,
        59,
        tzinfo=timezone.utc,
    )

    writer.append_alarm_transition(
        make_transition(
            transition_id="transition-001",
            timestamp=timestamp,
        )
    )

    path = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "alarm_transitions.jsonl"
    )

    assert path.exists()

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    payload = json.loads(lines[0])

    assert payload["transition_id"] == (
        "transition-001"
    )

    assert payload["record_type"] == (
        "alarm_transition"
    )


def test_append_does_not_truncate_existing_evidence(
    tmp_path,
) -> None:
    writer = JsonlEvidenceWriter(tmp_path)

    first_time = datetime(
        2026,
        9,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )

    second_time = datetime(
        2026,
        9,
        1,
        12,
        1,
        tzinfo=timezone.utc,
    )

    writer.append_event(
        make_event_record(
            event_id="event-001",
            timestamp=first_time,
        )
    )

    writer.append_event(
        make_event_record(
            event_id="event-002",
            timestamp=second_time,
        )
    )

    path = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "events.jsonl"
    )

    payloads = [
        json.loads(line)
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines()
    ]

    assert [
        item["event_id"]
        for item in payloads
    ] == [
        "event-001",
        "event-002",
    ]


def test_reopened_writer_continues_appending(
    tmp_path,
) -> None:
    timestamp = datetime(
        2026,
        9,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )

    first = JsonlEvidenceWriter(tmp_path)

    first.append_event(
        make_event_record(
            event_id="event-001",
            timestamp=timestamp,
        )
    )

    del first

    second = JsonlEvidenceWriter(tmp_path)

    second.append_event(
        make_event_record(
            event_id="event-002",
            timestamp=timestamp,
        )
    )

    path = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "events.jsonl"
    )

    payloads = [
        json.loads(line)
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines()
    ]

    assert [
        item["event_id"]
        for item in payloads
    ] == [
        "event-001",
        "event-002",
    ]


def test_midnight_rolls_to_new_utc_directory(
    tmp_path,
) -> None:
    writer = JsonlEvidenceWriter(tmp_path)

    before_midnight = datetime(
        2026,
        9,
        1,
        23,
        59,
        59,
        tzinfo=timezone.utc,
    )

    after_midnight = datetime(
        2026,
        9,
        2,
        0,
        0,
        1,
        tzinfo=timezone.utc,
    )

    writer.append_event(
        make_event_record(
            event_id="event-before",
            timestamp=before_midnight,
        )
    )

    writer.append_event(
        make_event_record(
            event_id="event-after",
            timestamp=after_midnight,
        )
    )

    day_one = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "events.jsonl"
    )

    day_two = (
        tmp_path
        / "2026"
        / "09"
        / "02"
        / "events.jsonl"
    )

    assert day_one.exists()
    assert day_two.exists()

    first_payload = json.loads(
        day_one.read_text(
            encoding="utf-8"
        ).strip()
    )

    second_payload = json.loads(
        day_two.read_text(
            encoding="utf-8"
        ).strip()
    )

    assert first_payload["event_id"] == (
        "event-before"
    )

    assert second_payload["event_id"] == (
        "event-after"
    )


def test_exact_event_retry_is_idempotent(
    tmp_path,
) -> None:
    writer = JsonlEvidenceWriter(tmp_path)

    timestamp = datetime(
        2026,
        9,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )

    record = make_event_record(
        event_id="event-retry",
        timestamp=timestamp,
    )

    writer.append_event(record)
    writer.append_event(record)

    path = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "events.jsonl"
    )

    assert len(
        path.read_text(
            encoding="utf-8"
        ).splitlines()
    ) == 1


def test_exact_transition_retry_is_idempotent(
    tmp_path,
) -> None:
    writer = JsonlEvidenceWriter(tmp_path)

    timestamp = datetime(
        2026,
        9,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )

    transition = make_transition(
        transition_id="transition-retry",
        timestamp=timestamp,
    )

    writer.append_alarm_transition(transition)
    writer.append_alarm_transition(transition)

    path = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "alarm_transitions.jsonl"
    )

    assert len(
        path.read_text(
            encoding="utf-8"
        ).splitlines()
    ) == 1


def test_conflicting_event_identity_is_rejected(
    tmp_path,
) -> None:
    import pytest

    from app.noc.history.jsonl_evidence_writer import (
        EvidenceConflictError,
    )

    writer = JsonlEvidenceWriter(tmp_path)

    first_time = datetime(
        2026,
        9,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )

    writer.append_event(
        make_event_record(
            event_id="event-conflict",
            timestamp=first_time,
        )
    )

    path = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "events.jsonl"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        ).strip()
    )

    payload["title"] = "Tampered title"

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        EvidenceConflictError
    ):
        writer.append_event(
            make_event_record(
                event_id="event-conflict",
                timestamp=first_time,
            )
        )


def test_reopened_writer_preserves_retry_idempotency(
    tmp_path,
) -> None:
    timestamp = datetime(
        2026,
        9,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )

    record = make_event_record(
        event_id="event-restart-retry",
        timestamp=timestamp,
    )

    first = JsonlEvidenceWriter(tmp_path)
    first.append_event(record)

    del first

    second = JsonlEvidenceWriter(tmp_path)
    second.append_event(record)

    path = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "events.jsonl"
    )

    assert len(
        path.read_text(
            encoding="utf-8"
        ).splitlines()
    ) == 1
