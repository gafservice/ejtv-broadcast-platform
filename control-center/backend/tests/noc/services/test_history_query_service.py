from datetime import datetime, timedelta, timezone

import pytest

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
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.history.alarm_transition import (
    AlarmTransition,
    AlarmTransitionType,
    make_alarm_transition_id,
)
from app.noc.history.event_history_record import (
    EventHistoryRecord,
)
from app.noc.history.memory_repository import (
    InMemoryAlarmHistoryRepository,
    InMemoryEventHistoryRepository,
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
from app.noc.services.history_query_service import (
    HistoryQueryService,
)


NOW = datetime(
    2026,
    9,
    1,
    18,
    0,
    tzinfo=timezone.utc,
)


def make_context():
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

    events = InMemoryEventHistoryRepository()
    alarms = InMemoryAlarmHistoryRepository()

    service = HistoryQueryService(
        event_repository=events,
        alarm_repository=alarms,
    )

    return node, instance, events, alarms, service


def make_event(
    instance_id: NodeInstanceId,
    *,
    event_id: str,
    timestamp: datetime,
) -> EventRecord:
    return EventRecord(
        event_id=event_id,
        event_type="TEST_EVENT",
        severity=EventSeverity.INFO,
        timestamp=timestamp,
        source=instance_id,
        title="Test event",
        description="Historical test event",
    )


def persist_event(
    events,
    node,
    instance,
    *,
    event_id: str,
    timestamp: datetime,
) -> EventRecord:
    event = make_event(
        instance.instance_id,
        event_id=event_id,
        timestamp=timestamp,
    )

    events.append(
        EventHistoryRecord(
            event=event,
            node_id=node.node_id,
            instance_id=instance.instance_id,
            recorded_at=timestamp,
        )
    )

    return event


def persist_alarm_transition(
    alarms,
    node,
    instance,
    *,
    alarm_id: str,
    timestamp: datetime,
) -> AlarmTransition:
    alarm = AlarmRecord(
        alarm_id=alarm_id,
        alarm_type="TEST_ALARM",
        severity=AlarmSeverity.CRITICAL,
        state=AlarmState.ACTIVE,
        timestamp=timestamp,
        source=instance.instance_id,
        title="Test alarm",
        description="Historical test alarm",
    )

    transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=alarm.alarm_id,
            transition_type=AlarmTransitionType.OPENED,
            timestamp=timestamp,
            source=instance.instance_id,
            state=alarm.state,
        ),
        alarm_id=alarm.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=timestamp,
        source=instance.instance_id,
        state=alarm.state,
    )

    alarms.record_lifecycle(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        alarm=alarm,
        transition=transition,
    )

    return transition


def test_last_24_hours_returns_events_and_alarm_transitions():
    node, instance, events, alarms, service = make_context()

    event = persist_event(
        events,
        node,
        instance,
        event_id="event-inside",
        timestamp=NOW - timedelta(hours=2),
    )

    transition = persist_alarm_transition(
        alarms,
        node,
        instance,
        alarm_id="alarm-inside",
        timestamp=NOW - timedelta(hours=1),
    )

    result = service.last_24_hours(
        now=NOW,
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert result.start == NOW - timedelta(hours=24)
    assert result.end == NOW
    assert result.events == (
        events.get(event.event_id),
    )
    assert result.alarm_transitions == (
        transition,
    )


def test_last_24_hours_uses_half_open_window():
    node, instance, events, _, service = make_context()

    at_start = persist_event(
        events,
        node,
        instance,
        event_id="event-at-start",
        timestamp=NOW - timedelta(hours=24),
    )

    persist_event(
        events,
        node,
        instance,
        event_id="event-at-end",
        timestamp=NOW,
    )

    result = service.last_24_hours(
        now=NOW,
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert tuple(
        record.event_id
        for record in result.events
    ) == (at_start.event_id,)


def test_last_24_hours_excludes_older_records():
    node, instance, events, alarms, service = make_context()

    persist_event(
        events,
        node,
        instance,
        event_id="event-old",
        timestamp=NOW - timedelta(hours=24, microseconds=1),
    )

    persist_alarm_transition(
        alarms,
        node,
        instance,
        alarm_id="alarm-old",
        timestamp=NOW - timedelta(hours=25),
    )

    result = service.last_24_hours(
        now=NOW,
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert result.events == ()
    assert result.alarm_transitions == ()


def test_last_24_hours_respects_instance_scope():
    node, instance, events, _, service = make_context()

    other_instance = node.create_instance(
        instance_id="streaming-secondary"
    )

    persist_event(
        events,
        node,
        instance,
        event_id="event-primary",
        timestamp=NOW - timedelta(minutes=10),
    )

    persist_event(
        events,
        node,
        other_instance,
        event_id="event-secondary",
        timestamp=NOW - timedelta(minutes=5),
    )

    result = service.last_24_hours(
        now=NOW,
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert tuple(
        record.event_id
        for record in result.events
    ) == ("event-primary",)


def test_last_24_hours_requires_utc_now():
    _, _, _, _, service = make_context()

    with pytest.raises(
        ValueError,
        match="UTC",
    ):
        service.last_24_hours(
            now=datetime(
                2026,
                9,
                1,
                18,
                0,
            ),
        )


def test_service_rejects_invalid_repositories():
    with pytest.raises(TypeError):
        HistoryQueryService(
            event_repository=object(),
            alarm_repository=InMemoryAlarmHistoryRepository(),
        )

    with pytest.raises(TypeError):
        HistoryQueryService(
            event_repository=InMemoryEventHistoryRepository(),
            alarm_repository=object(),
        )


def test_last_24_hours_survives_sqlite_repository_reopen(
    tmp_path,
):
    database_path = (
        tmp_path / "noc-history.sqlite3"
    )

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

    initial_database = SQLiteHistoryDatabase(
        database_path
    )

    initial_events = SQLiteEventHistoryRepository(
        initial_database
    )

    initial_alarms = SQLiteAlarmHistoryRepository(
        initial_database
    )

    inside_event = persist_event(
        initial_events,
        node,
        instance,
        event_id="event-sqlite-inside",
        timestamp=NOW - timedelta(hours=3),
    )

    inside_transition = persist_alarm_transition(
        initial_alarms,
        node,
        instance,
        alarm_id="alarm-sqlite-inside",
        timestamp=NOW - timedelta(hours=2),
    )

    persist_event(
        initial_events,
        node,
        instance,
        event_id="event-sqlite-old",
        timestamp=NOW - timedelta(hours=25),
    )

    persist_alarm_transition(
        initial_alarms,
        node,
        instance,
        alarm_id="alarm-sqlite-old",
        timestamp=NOW - timedelta(hours=26),
    )

    del initial_events
    del initial_alarms
    del initial_database

    reopened_database = SQLiteHistoryDatabase(
        database_path
    )

    reopened_events = SQLiteEventHistoryRepository(
        reopened_database
    )

    reopened_alarms = SQLiteAlarmHistoryRepository(
        reopened_database
    )

    service = HistoryQueryService(
        event_repository=reopened_events,
        alarm_repository=reopened_alarms,
    )

    result = service.last_24_hours(
        now=NOW,
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert result.start == NOW - timedelta(hours=24)
    assert result.end == NOW

    assert tuple(
        record.event_id
        for record in result.events
    ) == (
        inside_event.event_id,
    )

    assert result.alarm_transitions == (
        inside_transition,
    )


def test_recent_events_returns_durable_events_from_last_24_hours():
    node, instance, events, _, service = make_context()

    inside = persist_event(
        events,
        node,
        instance,
        event_id="event-recent",
        timestamp=NOW - timedelta(minutes=30),
    )

    persist_event(
        events,
        node,
        instance,
        event_id="event-old-for-recent",
        timestamp=NOW - timedelta(hours=25),
    )

    result = service.recent_events(
        now=NOW,
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert tuple(
        record.event
        for record in result
    ) == (inside,)


def test_active_alarms_returns_durable_active_alarm_state():
    node, instance, _, alarms, service = make_context()

    active = AlarmRecord(
        alarm_id="alarm-active-query",
        alarm_type="TEST_ALARM",
        severity=AlarmSeverity.CRITICAL,
        state=AlarmState.ACTIVE,
        timestamp=NOW - timedelta(minutes=5),
        source=instance.instance_id,
        title="Active alarm",
        description="Durable active alarm",
    )

    transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=active.alarm_id,
            transition_type=AlarmTransitionType.OPENED,
            timestamp=active.timestamp,
            source=instance.instance_id,
            state=active.state,
        ),
        alarm_id=active.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=active.timestamp,
        source=instance.instance_id,
        state=active.state,
    )

    alarms.record_lifecycle(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        alarm=active,
        transition=transition,
    )

    result = service.active_alarms(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert result == (active,)
