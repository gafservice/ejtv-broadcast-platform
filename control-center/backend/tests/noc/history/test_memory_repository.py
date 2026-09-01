from dataclasses import replace
from datetime import datetime, timezone

import pytest

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
from app.noc.history.memory_repository import (
    InMemoryAlarmHistoryRepository,
    InMemoryEventHistoryRepository,
)


T0 = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 9, 1, 12, 1, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 9, 1, 12, 2, 0, tzinfo=timezone.utc)
T3 = datetime(2026, 9, 1, 12, 3, 0, tzinfo=timezone.utc)

INSTANCE = NodeInstanceId("instance-001")

NODE = NodeId(
    id="node-001",
    name="node-001",
    display_name="Node 001",
    created_at=T0,
)


def make_event(
    event_id: str,
    timestamp: datetime,
) -> EventHistoryRecord:
    event = EventRecord(
        event_id=event_id,
        event_type="SESSION_CONNECTED",
        severity=EventSeverity.INFO,
        timestamp=timestamp,
        source=INSTANCE,
        title="Session connected",
        description="SRT reader connected",
    )

    return EventHistoryRecord(
        event=event,
        node_id=NODE,
        instance_id=INSTANCE,
        recorded_at=timestamp,
    )


def make_alarm(
    *,
    state: AlarmState = AlarmState.ACTIVE,
    acknowledged: bool = False,
    acknowledged_by: str | None = None,
    acknowledged_at: datetime | None = None,
    resolved_at: datetime | None = None,
    closed_at: datetime | None = None,
) -> AlarmRecord:
    return AlarmRecord(
        alarm_id="alarm-001",
        alarm_type="CRITICAL_PATH_TRAFFIC_STALLED",
        severity=AlarmSeverity.CRITICAL,
        state=state,
        timestamp=T0,
        source=INSTANCE,
        title="Traffic stalled",
        description="Inbound path traffic is stalled",
        acknowledged=acknowledged,
        acknowledged_by=acknowledged_by,
        acknowledged_at=acknowledged_at,
        resolved_at=resolved_at,
        closed_at=closed_at,
        attributes={"path": "ejtv"},
    )


def make_transition(
    transition_id: str,
    transition_type: AlarmTransitionType,
    timestamp: datetime,
    state: AlarmState,
) -> AlarmTransition:
    return AlarmTransition(
        transition_id=transition_id,
        alarm_id="alarm-001",
        transition_type=transition_type,
        timestamp=timestamp,
        source=INSTANCE,
        state=state,
    )


def test_event_repository_append_and_get() -> None:
    repository = InMemoryEventHistoryRepository()
    record = make_event("event-001", T1)

    repository.append(record)

    assert repository.get("event-001") == record


def test_event_repository_rejects_duplicate_event_id() -> None:
    repository = InMemoryEventHistoryRepository()
    record = make_event("event-001", T1)

    repository.append(record)

    with pytest.raises(ValueError):
        repository.append(record)


def test_event_repository_lists_between_in_time_order() -> None:
    repository = InMemoryEventHistoryRepository()

    repository.append(make_event("event-003", T3))
    repository.append(make_event("event-001", T1))
    repository.append(make_event("event-002", T2))

    records = repository.list_between(T1, T3)

    assert [record.event_id for record in records] == [
        "event-001",
        "event-002",
    ]


def test_event_repository_window_is_start_inclusive_end_exclusive() -> None:
    repository = InMemoryEventHistoryRepository()

    repository.append(make_event("event-start", T1))
    repository.append(make_event("event-end", T2))

    records = repository.list_between(T1, T2)

    assert [record.event_id for record in records] == [
        "event-start",
    ]


def test_alarm_repository_saves_and_replaces_current_state() -> None:
    repository = InMemoryAlarmHistoryRepository()

    active = make_alarm()

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=active,
    )

    acknowledged = replace(
        active,
        state=AlarmState.ACKNOWLEDGED,
        acknowledged=True,
        acknowledged_by="operator-01",
        acknowledged_at=T1,
    )

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=acknowledged,
    )

    current = repository.get_current("alarm-001")

    assert current is not None
    assert current.alarm_id == "alarm-001"
    assert current.state is AlarmState.ACKNOWLEDGED
    assert current.timestamp == T0


def test_alarm_repository_lists_active_and_acknowledged() -> None:
    repository = InMemoryAlarmHistoryRepository()

    active = make_alarm()

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=active,
    )

    assert repository.list_active() == (active,)

    acknowledged = replace(
        active,
        state=AlarmState.ACKNOWLEDGED,
        acknowledged=True,
        acknowledged_by="operator-01",
        acknowledged_at=T1,
    )

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=acknowledged,
    )

    assert repository.list_active() == (acknowledged,)


def test_alarm_repository_excludes_resolved_from_active() -> None:
    repository = InMemoryAlarmHistoryRepository()

    resolved = make_alarm(
        state=AlarmState.RESOLVED,
        resolved_at=T2,
    )

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=resolved,
    )

    assert repository.list_active() == ()


def test_alarm_repository_preserves_transition_history() -> None:
    repository = InMemoryAlarmHistoryRepository()

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=make_alarm(),
    )

    repository.append_transition(
        make_transition(
            "transition-002",
            AlarmTransitionType.RESOLVED,
            T2,
            AlarmState.RESOLVED,
        )
    )

    repository.append_transition(
        make_transition(
            "transition-001",
            AlarmTransitionType.OPENED,
            T0,
            AlarmState.ACTIVE,
        )
    )

    transitions = repository.list_transitions("alarm-001")

    assert [
        transition.transition_id
        for transition in transitions
    ] == [
        "transition-001",
        "transition-002",
    ]


def test_alarm_repository_rejects_duplicate_transition_id() -> None:
    repository = InMemoryAlarmHistoryRepository()

    transition = make_transition(
        "transition-001",
        AlarmTransitionType.OPENED,
        T0,
        AlarmState.ACTIVE,
    )

    repository.append_transition(transition)

    with pytest.raises(ValueError):
        repository.append_transition(transition)


def test_alarm_transition_window_is_start_inclusive_end_exclusive() -> None:
    repository = InMemoryAlarmHistoryRepository()

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=make_alarm(),
    )

    repository.append_transition(
        make_transition(
            "transition-start",
            AlarmTransitionType.OPENED,
            T1,
            AlarmState.ACTIVE,
        )
    )

    repository.append_transition(
        make_transition(
            "transition-end",
            AlarmTransitionType.RESOLVED,
            T2,
            AlarmState.RESOLVED,
        )
    )

    transitions = repository.list_transitions_between(
        T1,
        T2,
    )

    assert [
        transition.transition_id
        for transition in transitions
    ] == [
        "transition-start",
    ]


def test_alarm_repository_rejects_scope_change_for_same_alarm_id() -> None:
    repository = InMemoryAlarmHistoryRepository()

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=make_alarm(),
    )

    other_node = NodeId(
        id="node-002",
        name="node-002",
        display_name="Node 002",
        created_at=T0,
    )

    with pytest.raises(ValueError):
        repository.save_current(
            node_id=other_node,
            instance_id=INSTANCE,
            alarm=make_alarm(),
        )


def test_alarm_record_lifecycle_exact_retry_is_idempotent() -> None:
    repository = InMemoryAlarmHistoryRepository()

    alarm = make_alarm()

    transition = make_transition(
        "transition-idempotent",
        AlarmTransitionType.OPENED,
        T0,
        AlarmState.ACTIVE,
    )

    repository.record_lifecycle(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=alarm,
        transition=transition,
    )

    repository.record_lifecycle(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=alarm,
        transition=transition,
    )

    assert repository.get_current(
        alarm.alarm_id
    ) == alarm

    assert repository.list_transitions(
        alarm.alarm_id
    ) == (transition,)


def test_alarm_record_lifecycle_conflicting_retry_is_rejected() -> None:
    repository = InMemoryAlarmHistoryRepository()

    alarm = make_alarm()

    transition = make_transition(
        "transition-conflict",
        AlarmTransitionType.OPENED,
        T0,
        AlarmState.ACTIVE,
    )

    repository.record_lifecycle(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=alarm,
        transition=transition,
    )

    conflicting = AlarmTransition(
        transition_id=transition.transition_id,
        alarm_id=alarm.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=T1,
        source=INSTANCE,
        state=AlarmState.ACTIVE,
        actor=None,
        metadata=None,
    )

    with pytest.raises(
        ValueError,
        match="conflicting lifecycle data",
    ):
        repository.record_lifecycle(
            node_id=NODE,
            instance_id=INSTANCE,
            alarm=alarm,
            transition=conflicting,
        )

    assert repository.get_current(
        alarm.alarm_id
    ) == alarm

    assert repository.list_transitions(
        alarm.alarm_id
    ) == (transition,)
