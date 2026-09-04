"""SQLite integration tests for canonical NOC history CSV export."""

from __future__ import annotations

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
from app.noc.history.filesystem_csv_export_repository import (
    FilesystemCsvExportRepository,
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
from app.noc.services.history_csv_export_service import (
    HistoryCsvExportService,
)


NOW = datetime(
    2026,
    9,
    4,
    18,
    0,
    tzinfo=timezone.utc,
)


def make_node():
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

    return node, instance


def make_sqlite_context(database_path):
    database = SQLiteHistoryDatabase(
        database_path
    )

    events = SQLiteEventHistoryRepository(
        database
    )

    alarms = SQLiteAlarmHistoryRepository(
        database
    )

    service = HistoryCsvExportService(
        event_repository=events,
        alarm_repository=alarms,
        export_repository=(
            FilesystemCsvExportRepository()
        ),
    )

    return (
        database,
        events,
        alarms,
        service,
    )


def persist_event(
    events,
    node,
    instance,
    *,
    event_id,
    timestamp,
    attributes=None,
):
    event = EventRecord(
        event_id=event_id,
        event_type="TEST_EVENT",
        severity=EventSeverity.INFO,
        timestamp=timestamp,
        source=instance.instance_id,
        title="Test event",
        description="Historical SQLite event",
        correlation_id="corr-test",
        attributes=attributes,
    )

    record = EventHistoryRecord(
        event=event,
        node_id=node.node_id,
        instance_id=instance.instance_id,
        recorded_at=timestamp,
    )

    events.append(
        record
    )

    return record


def persist_alarm_transition(
    alarms,
    node,
    instance,
    *,
    alarm_id,
    timestamp,
    metadata=None,
):
    alarm = AlarmRecord(
        alarm_id=alarm_id,
        alarm_type="TEST_ALARM",
        severity=AlarmSeverity.CRITICAL,
        state=AlarmState.ACTIVE,
        timestamp=timestamp,
        source=instance.instance_id,
        title="Test alarm",
        description="Historical SQLite alarm",
    )

    transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=alarm.alarm_id,
            transition_type=(
                AlarmTransitionType.OPENED
            ),
            timestamp=timestamp,
            source=instance.instance_id,
            state=alarm.state,
        ),
        alarm_id=alarm.alarm_id,
        transition_type=(
            AlarmTransitionType.OPENED
        ),
        timestamp=timestamp,
        source=instance.instance_id,
        state=alarm.state,
        metadata=metadata,
    )

    alarms.record_lifecycle(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        alarm=alarm,
        transition=transition,
    )

    return transition


def test_sqlite_export_survives_reopen_and_is_deterministic(
    tmp_path,
):
    database_path = (
        tmp_path
        / "noc-history.sqlite3"
    )

    node, instance = make_node()

    (
        _,
        events,
        alarms,
        first_service,
    ) = make_sqlite_context(
        database_path
    )

    # Persist deliberately out of chronological order.
    persist_event(
        events,
        node,
        instance,
        event_id="event-002",
        timestamp=NOW - timedelta(hours=1),
        attributes={
            "z": "2",
            "a": "1",
        },
    )

    persist_event(
        events,
        node,
        instance,
        event_id="event-001",
        timestamp=NOW - timedelta(hours=2),
        attributes={
            "b": "two",
            "a": "one",
        },
    )

    persist_alarm_transition(
        alarms,
        node,
        instance,
        alarm_id="alarm-002",
        timestamp=NOW - timedelta(minutes=30),
        metadata={
            "z": "2",
            "a": "1",
        },
    )

    persist_alarm_transition(
        alarms,
        node,
        instance,
        alarm_id="alarm-001",
        timestamp=NOW - timedelta(hours=1),
        metadata={
            "b": "two",
            "a": "one",
        },
    )

    first = first_service.export_range(
        start=NOW - timedelta(hours=3),
        end=NOW,
        destination=(
            tmp_path
            / "export-first"
        ),
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    first_events = (
        first.events_file.read_bytes()
    )

    first_alarms = (
        first.alarm_transitions_file.read_bytes()
    )

    # Recreate the complete SQLite access path over the same DB.
    del first_service
    del events
    del alarms

    (
        _,
        reopened_events,
        reopened_alarms,
        reopened_service,
    ) = make_sqlite_context(
        database_path
    )

    second = reopened_service.export_range(
        start=NOW - timedelta(hours=3),
        end=NOW,
        destination=(
            tmp_path
            / "export-second"
        ),
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    second_events = (
        second.events_file.read_bytes()
    )

    second_alarms = (
        second.alarm_transitions_file.read_bytes()
    )

    assert second_events == first_events
    assert second_alarms == first_alarms

    events_text = first_events.decode(
        "utf-8"
    )

    alarms_text = first_alarms.decode(
        "utf-8"
    )

    assert events_text.index(
        "event-001"
    ) < events_text.index(
        "event-002"
    )

    assert alarms_text.index(
        "alarm-001"
    ) < alarms_text.index(
        "alarm-002"
    )

    assert (
        first.events_file.name
        == "events.csv"
    )

    assert (
        first.alarm_transitions_file.name
        == "alarm_transitions.csv"
    )

    assert (
        second.events_file.name
        == "events.csv"
    )

    assert (
        second.alarm_transitions_file.name
        == "alarm_transitions.csv"
    )

    # Keep references alive until all assertions finish.
    assert reopened_events is not None
    assert reopened_alarms is not None


def test_sqlite_export_respects_instance_scope_end_to_end(
    tmp_path,
):
    database_path = (
        tmp_path
        / "noc-history.sqlite3"
    )

    node, primary_instance = make_node()

    secondary_instance = node.create_instance(
        instance_id="streaming-secondary"
    )

    (
        _,
        events,
        alarms,
        service,
    ) = make_sqlite_context(
        database_path
    )

    persist_event(
        events,
        node,
        primary_instance,
        event_id="event-primary",
        timestamp=NOW - timedelta(minutes=40),
    )

    persist_event(
        events,
        node,
        secondary_instance,
        event_id="event-secondary",
        timestamp=NOW - timedelta(minutes=30),
    )

    persist_alarm_transition(
        alarms,
        node,
        primary_instance,
        alarm_id="alarm-primary",
        timestamp=NOW - timedelta(minutes=20),
    )

    persist_alarm_transition(
        alarms,
        node,
        secondary_instance,
        alarm_id="alarm-secondary",
        timestamp=NOW - timedelta(minutes=10),
    )

    result = service.export_range(
        start=NOW - timedelta(hours=1),
        end=NOW,
        destination=(
            tmp_path
            / "export-primary"
        ),
        node_id=node.node_id,
        instance_id=primary_instance.instance_id,
    )

    events_text = result.events_file.read_text(
        encoding="utf-8"
    )

    alarms_text = (
        result.alarm_transitions_file.read_text(
            encoding="utf-8"
        )
    )

    assert "event-primary" in events_text
    assert "event-secondary" not in events_text

    assert "alarm-primary" in alarms_text
    assert "alarm-secondary" not in alarms_text
