"""
Signal Health durable-history integration contract.

Signal Health does not own a separate history subsystem.

Its EventRecord and AlarmRecord objects must remain ordinary NOC records
and preserve their Signal Health identity and transition context through
the existing SQLite repositories and HistoryQueryService.
"""

import json
from datetime import datetime, timedelta, timezone

from app.noc.domain.node import Node
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
from app.noc.domain.node_type import NodeType
from app.noc.history.alarm_transition import (
    AlarmTransition,
    AlarmTransitionType,
    make_alarm_transition_id,
)
from app.noc.history.event_history_record import (
    EventHistoryRecord,
)
from app.noc.history.jsonl_evidence_writer import (
    JsonlEvidenceWriter,
)
from app.noc.history.sqlite_alarm_repository import (
    SQLiteAlarmHistoryRepository,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)
from app.noc.history.sqlite_event_repository import (
    SQLiteEventHistoryRepository,
)
from app.noc.services.evidence_reconciliation_service import (
    EvidenceReconciliationService,
)
from app.noc.services.history_query_service import (
    HistoryQueryService,
)


NOW = datetime(
    2026,
    9,
    26,
    3,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT = NOW - timedelta(minutes=30)


def test_signal_health_records_round_trip_through_generic_history(
    tmp_path,
):
    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
            created_at=NOW - timedelta(days=30),
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    database_path = tmp_path / "noc-history.db"

    database = SQLiteHistoryDatabase(
        database_path
    )

    events = SQLiteEventHistoryRepository(
        database
    )

    alarms = SQLiteAlarmHistoryRepository(
        database
    )

    attributes = {
        "profile_id": "impact-main",
        "service_id": "impact",
        "path_name": "impact",
        "previous": "HEALTHY",
        "current": "CRITICAL",
        "transition": "DEGRADED",
        "media_previous": "HEALTHY",
        "media_current": "HEALTHY",
        "transport_previous": "HEALTHY",
        "transport_current": "CRITICAL",
    }

    event = EventRecord(
        event_id="event-signal-health-contract",
        event_type="SIGNAL_HEALTH_DEGRADED",
        severity=EventSeverity.CRITICAL,
        timestamp=OBSERVED_AT,
        source=instance.instance_id,
        title="Signal Health DEGRADED: impact-main",
        description=(
            "Signal Health profile impact-main changed "
            "from HEALTHY to CRITICAL."
        ),
        correlation_id=None,
        attributes=attributes,
    )

    events.append(
        EventHistoryRecord(
            event=event,
            node_id=node.node_id,
            instance_id=instance.instance_id,
            recorded_at=OBSERVED_AT,
        )
    )

    alarm = AlarmRecord(
        alarm_id="alarm-signal-health-contract",
        alarm_type="SIGNAL_HEALTH",
        severity=AlarmSeverity.CRITICAL,
        state=AlarmState.ACTIVE,
        timestamp=OBSERVED_AT,
        source=instance.instance_id,
        title=(
            "Signal Health requires operator attention: "
            "impact-main / CRITICAL"
        ),
        description=(
            "Signal Health profile impact-main requires "
            "operator attention."
        ),
        attributes=attributes,
    )

    transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=alarm.alarm_id,
            transition_type=AlarmTransitionType.OPENED,
            timestamp=OBSERVED_AT,
            source=instance.instance_id,
            state=alarm.state,
        ),
        alarm_id=alarm.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=OBSERVED_AT,
        source=instance.instance_id,
        state=alarm.state,
        metadata=attributes,
    )

    alarms.record_lifecycle(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        alarm=alarm,
        transition=transition,
    )

    del events
    del alarms
    del database

    reopened_database = SQLiteHistoryDatabase(
        database_path
    )

    reopened_events = SQLiteEventHistoryRepository(
        reopened_database
    )

    reopened_alarms = SQLiteAlarmHistoryRepository(
        reopened_database
    )

    history = HistoryQueryService(
        event_repository=reopened_events,
        alarm_repository=reopened_alarms,
    )

    result = history.last_24_hours(
        now=NOW,
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert len(result.events) == 1

    recovered_event_record = result.events[0]
    recovered_event = recovered_event_record.event

    assert recovered_event.event_type == (
        "SIGNAL_HEALTH_DEGRADED"
    )

    assert recovered_event.severity is (
        EventSeverity.CRITICAL
    )

    assert recovered_event.timestamp == OBSERVED_AT
    assert recovered_event.source == instance.instance_id

    assert dict(recovered_event.attributes) == attributes

    assert recovered_event_record.node_id == node.node_id

    assert recovered_event_record.instance_id == (
        instance.instance_id
    )

    assert len(result.alarm_transitions) == 1

    recovered_transition = result.alarm_transitions[0]

    assert recovered_transition.alarm_id == (
        alarm.alarm_id
    )

    assert recovered_transition.transition_type is (
        AlarmTransitionType.OPENED
    )

    assert recovered_transition.timestamp == OBSERVED_AT

    assert recovered_transition.source == (
        instance.instance_id
    )

    assert recovered_transition.state is (
        AlarmState.ACTIVE
    )

    assert dict(recovered_transition.metadata) == attributes

    recovered_alarm = reopened_alarms.get_current(
        alarm.alarm_id
    )

    assert recovered_alarm is not None

    assert recovered_alarm.alarm_type == (
        "SIGNAL_HEALTH"
    )

    assert recovered_alarm.severity is (
        AlarmSeverity.CRITICAL
    )

    assert recovered_alarm.state is AlarmState.ACTIVE
    assert recovered_alarm.timestamp == OBSERVED_AT

    assert recovered_alarm.source == (
        instance.instance_id
    )

    assert dict(recovered_alarm.attributes) == attributes

    active = history.active_alarms(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert active == (recovered_alarm,)


def test_signal_health_evidence_is_reconstructed_from_durable_history(
    tmp_path,
):
    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
            created_at=NOW - timedelta(days=30),
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    database_path = (
        tmp_path
        / "history"
        / "noc-history.db"
    )

    database = SQLiteHistoryDatabase(
        database_path
    )

    events = SQLiteEventHistoryRepository(
        database
    )

    alarms = SQLiteAlarmHistoryRepository(
        database
    )

    attributes = {
        "profile_id": "impact-main",
        "service_id": "impact",
        "path_name": "impact",
        "previous": "HEALTHY",
        "current": "CRITICAL",
        "transition": "DEGRADED",
        "media_previous": "HEALTHY",
        "media_current": "HEALTHY",
        "transport_previous": "HEALTHY",
        "transport_current": "CRITICAL",
    }

    event = EventRecord(
        event_id="event-signal-health-evidence-contract",
        event_type="SIGNAL_HEALTH_DEGRADED",
        severity=EventSeverity.CRITICAL,
        timestamp=OBSERVED_AT,
        source=instance.instance_id,
        title="Signal Health DEGRADED: impact-main",
        description=(
            "Signal Health profile impact-main changed "
            "from HEALTHY to CRITICAL."
        ),
        correlation_id=None,
        attributes=attributes,
    )

    event_record = EventHistoryRecord(
        event=event,
        node_id=node.node_id,
        instance_id=instance.instance_id,
        recorded_at=OBSERVED_AT,
    )

    events.append(event_record)

    alarm = AlarmRecord(
        alarm_id="alarm-signal-health-evidence-contract",
        alarm_type="SIGNAL_HEALTH",
        severity=AlarmSeverity.CRITICAL,
        state=AlarmState.ACTIVE,
        timestamp=OBSERVED_AT,
        source=instance.instance_id,
        title=(
            "Signal Health requires operator attention: "
            "impact-main / CRITICAL"
        ),
        description=(
            "Signal Health profile impact-main requires "
            "operator attention."
        ),
        attributes=attributes,
    )

    transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=alarm.alarm_id,
            transition_type=AlarmTransitionType.OPENED,
            timestamp=OBSERVED_AT,
            source=instance.instance_id,
            state=alarm.state,
        ),
        alarm_id=alarm.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=OBSERVED_AT,
        source=instance.instance_id,
        state=alarm.state,
        metadata=attributes,
    )

    alarms.record_lifecycle(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        alarm=alarm,
        transition=transition,
    )

    evidence_root = tmp_path / "evidence"

    assert not evidence_root.exists()

    writer = JsonlEvidenceWriter(
        evidence_root
    )

    reconciliation = EvidenceReconciliationService(
        event_repository=events,
        alarm_repository=alarms,
        evidence_writer=writer,
    )

    result = reconciliation.reconcile_between(
        start=OBSERVED_AT - timedelta(minutes=1),
        end=OBSERVED_AT + timedelta(minutes=1),
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert result.events_replayed == 1

    assert (
        result.alarm_transitions_replayed
        == 1
    )

    day_root = (
        evidence_root
        / OBSERVED_AT.strftime("%Y")
        / OBSERVED_AT.strftime("%m")
        / OBSERVED_AT.strftime("%d")
    )

    event_path = day_root / "events.jsonl"

    transition_path = (
        day_root
        / "alarm_transitions.jsonl"
    )

    assert event_path.exists()
    assert transition_path.exists()

    event_lines = event_path.read_text(
        encoding="utf-8"
    ).splitlines()

    transition_lines = transition_path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(event_lines) == 1
    assert len(transition_lines) == 1

    event_payload = json.loads(
        event_lines[0]
    )

    transition_payload = json.loads(
        transition_lines[0]
    )

    assert event_payload["event_id"] == (
        event.event_id
    )

    assert event_payload["event_type"] == (
        "SIGNAL_HEALTH_DEGRADED"
    )

    assert event_payload["severity"] == (
        "CRITICAL"
    )

    assert event_payload["source"] == (
        str(instance.instance_id)
    )

    assert event_payload["attributes"] == (
        attributes
    )

    assert transition_payload["transition_id"] == (
        transition.transition_id
    )

    assert transition_payload["alarm_id"] == (
        alarm.alarm_id
    )

    assert transition_payload["transition_type"] == (
        "OPENED"
    )

    assert transition_payload["state"] == (
        "ACTIVE"
    )

    assert transition_payload["source"] == (
        str(instance.instance_id)
    )

    assert transition_payload["metadata"] == (
        attributes
    )

    second = reconciliation.reconcile_between(
        start=OBSERVED_AT - timedelta(minutes=1),
        end=OBSERVED_AT + timedelta(minutes=1),
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert second.events_replayed == 1

    assert (
        second.alarm_transitions_replayed
        == 1
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
