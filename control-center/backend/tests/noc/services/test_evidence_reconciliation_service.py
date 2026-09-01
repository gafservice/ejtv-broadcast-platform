"""Tests for durable-history to JSONL evidence reconciliation."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
)
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
from app.noc.history.memory_repository import (
    InMemoryAlarmHistoryRepository,
    InMemoryEventHistoryRepository,
)
from app.noc.services.evidence_reconciliation_service import (
    EvidenceReconciliationService,
)


BASE_TIME = datetime(
    2026,
    9,
    1,
    12,
    0,
    tzinfo=timezone.utc,
)

NODE_ID = NodeId.create(
    id="streaming-core",
    name="streaming",
    display_name="Streaming Core",
)

INSTANCE_ID = NodeInstanceId(
    "streaming-primary"
)


def make_event_record() -> EventHistoryRecord:
    event = EventRecord(
        event_id="event-reconcile-001",
        event_type="SESSION_CONNECTED",
        severity=EventSeverity.INFO,
        timestamp=BASE_TIME,
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
        recorded_at=BASE_TIME,
    )


def make_alarm_and_transition():
    alarm = AlarmRecord(
        alarm_id="alarm-reconcile-001",
        alarm_type="CRITICAL_PATH_TRAFFIC_STALLED",
        severity=AlarmSeverity.CRITICAL,
        state=AlarmState.ACTIVE,
        timestamp=BASE_TIME,
        source=INSTANCE_ID,
        title="Traffic stalled",
        description="Inbound bitrate is zero.",
        attributes={
            "path": "ejtv",
        },
    )

    transition = AlarmTransition(
        transition_id="transition-reconcile-001",
        alarm_id=alarm.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=BASE_TIME,
        source=INSTANCE_ID,
        state=AlarmState.ACTIVE,
        metadata=alarm.attributes,
    )

    return alarm, transition


def test_reconcile_replays_durable_history_to_jsonl(
    tmp_path,
) -> None:
    events = InMemoryEventHistoryRepository()
    alarms = InMemoryAlarmHistoryRepository()
    writer = JsonlEvidenceWriter(tmp_path)

    event_record = make_event_record()
    alarm, transition = make_alarm_and_transition()

    events.append(event_record)

    alarms.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=alarm,
        transition=transition,
    )

    service = EvidenceReconciliationService(
        event_repository=events,
        alarm_repository=alarms,
        evidence_writer=writer,
    )

    result = service.reconcile_between(
        start=BASE_TIME - timedelta(minutes=1),
        end=BASE_TIME + timedelta(minutes=1),
    )

    assert result.events_replayed == 1
    assert result.alarm_transitions_replayed == 1

    event_path = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "events.jsonl"
    )

    transition_path = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "alarm_transitions.jsonl"
    )

    event_payload = json.loads(
        event_path.read_text(
            encoding="utf-8"
        ).strip()
    )

    transition_payload = json.loads(
        transition_path.read_text(
            encoding="utf-8"
        ).strip()
    )

    assert event_payload["event_id"] == (
        "event-reconcile-001"
    )

    assert transition_payload["transition_id"] == (
        "transition-reconcile-001"
    )


def test_reconcile_is_idempotent(
    tmp_path,
) -> None:
    events = InMemoryEventHistoryRepository()
    alarms = InMemoryAlarmHistoryRepository()
    writer = JsonlEvidenceWriter(tmp_path)

    event_record = make_event_record()
    alarm, transition = make_alarm_and_transition()

    events.append(event_record)

    alarms.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=alarm,
        transition=transition,
    )

    service = EvidenceReconciliationService(
        event_repository=events,
        alarm_repository=alarms,
        evidence_writer=writer,
    )

    kwargs = dict(
        start=BASE_TIME - timedelta(minutes=1),
        end=BASE_TIME + timedelta(minutes=1),
    )

    service.reconcile_between(**kwargs)
    service.reconcile_between(**kwargs)

    event_path = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "events.jsonl"
    )

    transition_path = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "alarm_transitions.jsonl"
    )

    assert len(
        event_path.read_text(
            encoding="utf-8"
        ).splitlines()
    ) == 1

    assert len(
        transition_path.read_text(
            encoding="utf-8"
        ).splitlines()
    ) == 1


def test_reconcile_respects_half_open_window(
    tmp_path,
) -> None:
    events = InMemoryEventHistoryRepository()
    alarms = InMemoryAlarmHistoryRepository()
    writer = JsonlEvidenceWriter(tmp_path)

    event_record = make_event_record()
    events.append(event_record)

    service = EvidenceReconciliationService(
        event_repository=events,
        alarm_repository=alarms,
        evidence_writer=writer,
    )

    result = service.reconcile_between(
        start=BASE_TIME - timedelta(minutes=1),
        end=BASE_TIME,
    )

    assert result.events_replayed == 0
    assert result.alarm_transitions_replayed == 0


def test_reconcile_can_restore_missing_jsonl_after_restart(
    tmp_path,
) -> None:
    events = InMemoryEventHistoryRepository()
    alarms = InMemoryAlarmHistoryRepository()

    event_record = make_event_record()
    events.append(event_record)

    # Simulates SQLite surviving while JSONL was never written.
    writer = JsonlEvidenceWriter(tmp_path)

    service = EvidenceReconciliationService(
        event_repository=events,
        alarm_repository=alarms,
        evidence_writer=writer,
    )

    result = service.reconcile_between(
        start=BASE_TIME - timedelta(hours=1),
        end=BASE_TIME + timedelta(hours=1),
    )

    assert result.events_replayed == 1

    path = (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / "events.jsonl"
    )

    assert path.exists()
