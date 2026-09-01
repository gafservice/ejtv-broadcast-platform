import sqlite3
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.alarm_transition import (
    AlarmTransition,
    AlarmTransitionType,
)
from app.noc.history.repository import (
    AlarmHistoryRepository,
)
from app.noc.history.sqlite_alarm_repository import (
    SQLiteAlarmHistoryRepository,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
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
        correlation_id="corr-001",
        attributes={
            "path": "ejtv",
            "protocol": "SRT",
        },
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
        actor="operator-01",
        metadata={
            "path": "ejtv",
        },
    )


def make_repository(
    tmp_path,
) -> SQLiteAlarmHistoryRepository:
    return SQLiteAlarmHistoryRepository(
        SQLiteHistoryDatabase(
            tmp_path / "history.sqlite3"
        )
    )


def test_repository_satisfies_protocol(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    assert isinstance(
        repository,
        AlarmHistoryRepository,
    )


def test_save_and_get_current_round_trip(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    alarm = make_alarm()

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=alarm,
    )

    loaded = repository.get_current(
        "alarm-001"
    )

    assert loaded == alarm


def test_alarm_survives_repository_recreation(
    tmp_path,
) -> None:
    path = tmp_path / "history.sqlite3"

    repository = SQLiteAlarmHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=make_alarm(),
    )

    del repository

    reopened = SQLiteAlarmHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    loaded = reopened.get_current(
        "alarm-001"
    )

    assert loaded is not None
    assert loaded.alarm_id == "alarm-001"
    assert loaded.state is AlarmState.ACTIVE


def test_save_current_replaces_state_without_changing_alarm_id(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

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

    loaded = repository.get_current(
        "alarm-001"
    )

    assert loaded == acknowledged
    assert loaded.timestamp == T0


def test_list_active_includes_active_and_acknowledged(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=make_alarm(),
    )

    assert len(repository.list_active()) == 1

    acknowledged = make_alarm(
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

    active = repository.list_active()

    assert len(active) == 1
    assert active[0].state is AlarmState.ACKNOWLEDGED


def test_list_active_excludes_resolved(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=make_alarm(
            state=AlarmState.RESOLVED,
            resolved_at=T2,
        ),
    )

    assert repository.list_active() == ()


def test_transition_round_trip_and_order(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

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

    transitions = repository.list_transitions(
        "alarm-001"
    )

    assert [
        transition.transition_id
        for transition in transitions
    ] == [
        "transition-001",
        "transition-002",
    ]

    assert transitions[0].metadata == {
        "path": "ejtv"
    }


def test_transition_survives_repository_recreation(
    tmp_path,
) -> None:
    path = tmp_path / "history.sqlite3"

    repository = SQLiteAlarmHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=make_alarm(),
    )

    repository.append_transition(
        make_transition(
            "transition-001",
            AlarmTransitionType.OPENED,
            T0,
            AlarmState.ACTIVE,
        )
    )

    del repository

    reopened = SQLiteAlarmHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    transitions = reopened.list_transitions(
        "alarm-001"
    )

    assert len(transitions) == 1
    assert transitions[0].transition_id == (
        "transition-001"
    )


def test_duplicate_transition_is_rejected(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=make_alarm(),
    )

    transition = make_transition(
        "transition-001",
        AlarmTransitionType.OPENED,
        T0,
        AlarmState.ACTIVE,
    )

    repository.append_transition(
        transition
    )

    with pytest.raises(ValueError):
        repository.append_transition(
            transition
        )


def test_transition_requires_existing_alarm(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    transition = make_transition(
        "transition-001",
        AlarmTransitionType.OPENED,
        T0,
        AlarmState.ACTIVE,
    )

    with pytest.raises(sqlite3.IntegrityError):
        repository.append_transition(
            transition
        )


def test_transition_window_is_start_inclusive_end_exclusive(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

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


def test_scope_change_for_same_alarm_id_is_rejected(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

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


def test_restart_recovers_active_alarm(
    tmp_path,
) -> None:
    path = tmp_path / "history.sqlite3"

    repository = SQLiteAlarmHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    alarm = make_alarm()

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=alarm,
    )

    repository.append_transition(
        make_transition(
            "transition-opened",
            AlarmTransitionType.OPENED,
            T0,
            AlarmState.ACTIVE,
        )
    )

    del repository

    reopened = SQLiteAlarmHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    active = reopened.list_active(
        node_id=NODE,
        instance_id=INSTANCE,
    )

    assert len(active) == 1
    assert active[0] == alarm

    transitions = reopened.list_transitions(
        "alarm-001"
    )

    assert len(transitions) == 1
    assert transitions[0].transition_type is (
        AlarmTransitionType.OPENED
    )


def test_restart_recovers_acknowledged_alarm(
    tmp_path,
) -> None:
    path = tmp_path / "history.sqlite3"

    repository = SQLiteAlarmHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    acknowledged = make_alarm(
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

    del repository

    reopened = SQLiteAlarmHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    active = reopened.list_active(
        node_id=NODE,
        instance_id=INSTANCE,
    )

    assert len(active) == 1
    assert active[0].state is AlarmState.ACKNOWLEDGED
    assert active[0].acknowledged_by == "operator-01"
    assert active[0].acknowledged_at == T1


def test_restart_does_not_recover_resolved_as_active(
    tmp_path,
) -> None:
    path = tmp_path / "history.sqlite3"

    repository = SQLiteAlarmHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    resolved = make_alarm(
        state=AlarmState.RESOLVED,
        resolved_at=T2,
    )

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=resolved,
    )

    del repository

    reopened = SQLiteAlarmHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    assert reopened.list_active(
        node_id=NODE,
        instance_id=INSTANCE,
    ) == ()

    loaded = reopened.get_current(
        "alarm-001"
    )

    assert loaded is not None
    assert loaded.state is AlarmState.RESOLVED
    assert loaded.resolved_at == T2


def test_transition_query_rejects_non_utc_window(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    costa_rica = timezone(
        timedelta(hours=-6)
    )

    start = datetime(
        2026,
        9,
        1,
        6,
        0,
        0,
        tzinfo=costa_rica,
    )

    end = datetime(
        2026,
        9,
        1,
        7,
        0,
        0,
        tzinfo=costa_rica,
    )

    with pytest.raises(ValueError):
        repository.list_transitions_between(
            start,
            end,
        )


def test_record_lifecycle_rolls_back_alarm_when_transition_fails(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    active = make_alarm()

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=active,
    )

    duplicate_transition = make_transition(
        "transition-duplicate",
        AlarmTransitionType.OPENED,
        T0,
        AlarmState.ACTIVE,
    )

    repository.append_transition(
        duplicate_transition
    )

    acknowledged = replace(
        active,
        state=AlarmState.ACKNOWLEDGED,
        acknowledged=True,
        acknowledged_by="operator-01",
        acknowledged_at=T1,
    )

    conflicting_transition = AlarmTransition(
        transition_id="transition-duplicate",
        alarm_id=acknowledged.alarm_id,
        transition_type=AlarmTransitionType.ACKNOWLEDGED,
        timestamp=T1,
        source=INSTANCE,
        state=AlarmState.ACKNOWLEDGED,
        actor="operator-01",
        metadata={
            "path": "ejtv",
        },
    )

    with pytest.raises(ValueError):
        repository.record_lifecycle(
            node_id=NODE,
            instance_id=INSTANCE,
            alarm=acknowledged,
            transition=conflicting_transition,
        )

    loaded = repository.get_current(
        "alarm-001"
    )

    assert loaded == active

    transitions = repository.list_transitions(
        "alarm-001"
    )

    assert transitions == (
        duplicate_transition,
    )


def test_alarm_attributes_none_round_trip_exactly(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    alarm = replace(
        make_alarm(),
        attributes=None,
    )

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=alarm,
    )

    loaded = repository.get_current(
        alarm.alarm_id
    )

    assert loaded == alarm
    assert loaded is not None
    assert loaded.attributes is None


def test_alarm_empty_attributes_round_trip_exactly(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    alarm = replace(
        make_alarm(),
        attributes={},
    )

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=alarm,
    )

    loaded = repository.get_current(
        alarm.alarm_id
    )

    assert loaded == alarm
    assert loaded is not None
    assert loaded.attributes is not None
    assert dict(loaded.attributes) == {}


def test_transition_metadata_none_round_trip_exactly(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    alarm = make_alarm()

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=alarm,
    )

    transition = AlarmTransition(
        transition_id="transition-none-metadata",
        alarm_id=alarm.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=T0,
        source=INSTANCE,
        state=AlarmState.ACTIVE,
        actor=None,
        metadata=None,
    )

    repository.append_transition(
        transition
    )

    loaded = repository.list_transitions(
        alarm.alarm_id
    )

    assert loaded == (transition,)
    assert loaded[0].metadata is None


def test_transition_empty_metadata_round_trip_exactly(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    alarm = make_alarm()

    repository.save_current(
        node_id=NODE,
        instance_id=INSTANCE,
        alarm=alarm,
    )

    transition = AlarmTransition(
        transition_id="transition-empty-metadata",
        alarm_id=alarm.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=T0,
        source=INSTANCE,
        state=AlarmState.ACTIVE,
        actor=None,
        metadata={},
    )

    repository.append_transition(
        transition
    )

    loaded = repository.list_transitions(
        alarm.alarm_id
    )

    assert loaded == (transition,)
    assert loaded[0].metadata is not None
    assert dict(loaded[0].metadata) == {}


def test_record_lifecycle_exact_retry_is_idempotent(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

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


def test_record_lifecycle_conflicting_retry_is_rejected(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

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
