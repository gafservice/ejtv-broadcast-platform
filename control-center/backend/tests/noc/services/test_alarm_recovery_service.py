from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.history.alarm_transition import (
    AlarmTransition,
    AlarmTransitionType,
    make_alarm_transition_id,
)
from app.noc.history.memory_repository import (
    InMemoryAlarmHistoryRepository,
)
from app.noc.history.sqlite_alarm_repository import (
    SQLiteAlarmHistoryRepository,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)
from app.noc.infrastructure.memory_repository import (
    InMemoryNodeRepository,
)
from app.noc.registry.registry import NodeRegistry
from app.noc.services.alarm_recovery_service import (
    AlarmRecoveryService,
)


BASE_TIME = datetime(
    2026,
    9,
    1,
    12,
    0,
    tzinfo=timezone.utc,
)


def make_context():
    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    history = InMemoryAlarmHistoryRepository()

    service = AlarmRecoveryService(
        registry=registry,
        history_repository=history,
    )

    return (
        repository,
        registry,
        node,
        instance,
        history,
        service,
    )


def make_alarm(
    *,
    state: AlarmState = AlarmState.ACTIVE,
) -> AlarmRecord:
    acknowledged = (
        state is AlarmState.ACKNOWLEDGED
    )

    return AlarmRecord(
        alarm_id="alarm-001",
        alarm_type="TEST_ALARM",
        severity=AlarmSeverity.CRITICAL,
        state=state,
        timestamp=BASE_TIME,
        source=NodeInstanceId(
            "streaming-primary"
        ),
        title="Test alarm",
        description="Test durable alarm",
        acknowledged=acknowledged,
        acknowledged_by=(
            "operator"
            if acknowledged
            else None
        ),
        acknowledged_at=(
            BASE_TIME
            if acknowledged
            else None
        ),
    )


def persist_opened_alarm(
    history,
    node,
    instance,
    alarm,
) -> None:
    transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=alarm.alarm_id,
            transition_type=AlarmTransitionType.OPENED,
            timestamp=alarm.timestamp,
            source=instance.instance_id,
            state=alarm.state,
        ),
        alarm_id=alarm.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=alarm.timestamp,
        source=instance.instance_id,
        state=alarm.state,
    )

    history.record_lifecycle(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        alarm=alarm,
        transition=transition,
    )


def test_recover_restores_active_alarm() -> None:
    (
        _,
        _,
        node,
        instance,
        history,
        service,
    ) = make_context()

    alarm = make_alarm()

    persist_opened_alarm(
        history,
        node,
        instance,
        alarm,
    )

    assert instance.alarms == ()

    recovered_at = (
        BASE_TIME + timedelta(minutes=5)
    )

    result = service.recover(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        timestamp=recovered_at,
    )

    assert result.recovered_count == 1
    assert result.recovered == (alarm,)
    assert instance.alarms == (alarm,)

    current = history.get_current(
        alarm.alarm_id
    )

    assert current == alarm
    assert current.state is AlarmState.ACTIVE

    transitions = history.list_transitions(
        alarm.alarm_id
    )

    assert len(transitions) == 2

    opened, recovered = transitions

    assert (
        opened.transition_type
        is AlarmTransitionType.OPENED
    )

    assert (
        recovered.transition_type
        is AlarmTransitionType.RECOVERED_AT_STARTUP
    )

    assert recovered.alarm_id == alarm.alarm_id
    assert recovered.timestamp == recovered_at
    assert recovered.state is AlarmState.ACTIVE
    assert recovered.source == instance.instance_id


def test_recover_preserves_acknowledged_alarm_state() -> None:
    (
        _,
        _,
        node,
        instance,
        history,
        service,
    ) = make_context()

    alarm = make_alarm(
        state=AlarmState.ACKNOWLEDGED
    )

    transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=alarm.alarm_id,
            transition_type=(
                AlarmTransitionType.ACKNOWLEDGED
            ),
            timestamp=alarm.timestamp,
            source=instance.instance_id,
            state=alarm.state,
        ),
        alarm_id=alarm.alarm_id,
        transition_type=(
            AlarmTransitionType.ACKNOWLEDGED
        ),
        timestamp=alarm.timestamp,
        source=instance.instance_id,
        state=alarm.state,
        actor="operator",
    )

    history.record_lifecycle(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        alarm=alarm,
        transition=transition,
    )

    recovered_at = (
        BASE_TIME + timedelta(minutes=10)
    )

    result = service.recover(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        timestamp=recovered_at,
    )

    assert result.recovered_count == 1
    assert instance.alarms == (alarm,)

    current = history.get_current(
        alarm.alarm_id
    )

    assert current is not None
    assert current.state is AlarmState.ACKNOWLEDGED

    transitions = history.list_transitions(
        alarm.alarm_id
    )

    assert len(transitions) == 2

    recovered = transitions[-1]

    assert (
        recovered.transition_type
        is AlarmTransitionType.RECOVERED_AT_STARTUP
    )
    assert recovered.state is AlarmState.ACKNOWLEDGED
    assert recovered.alarm_id == alarm.alarm_id


def test_recover_is_idempotent_when_called_twice_in_same_runtime() -> None:
    (
        _,
        _,
        node,
        instance,
        history,
        service,
    ) = make_context()

    alarm = make_alarm()

    persist_opened_alarm(
        history,
        node,
        instance,
        alarm,
    )

    recovered_at = (
        BASE_TIME + timedelta(minutes=5)
    )

    first = service.recover(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        timestamp=recovered_at,
    )

    second = service.recover(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        timestamp=recovered_at,
    )

    assert first.recovered_count == 1
    assert second.recovered_count == 0
    assert instance.alarms == (alarm,)

    transitions = history.list_transitions(
        alarm.alarm_id
    )

    recovered = [
        item
        for item in transitions
        if (
            item.transition_type
            is AlarmTransitionType.RECOVERED_AT_STARTUP
        )
    ]

    assert len(recovered) == 1


def test_recover_rejects_conflicting_live_alarm() -> None:
    (
        _,
        _,
        node,
        instance,
        history,
        service,
    ) = make_context()

    durable_alarm = make_alarm()

    persist_opened_alarm(
        history,
        node,
        instance,
        durable_alarm,
    )

    conflicting_alarm = AlarmRecord(
        alarm_id=durable_alarm.alarm_id,
        alarm_type=durable_alarm.alarm_type,
        severity=AlarmSeverity.MINOR,
        state=AlarmState.ACTIVE,
        timestamp=durable_alarm.timestamp,
        source=instance.instance_id,
        title=durable_alarm.title,
        description=durable_alarm.description,
    )

    instance.alarms = (
        conflicting_alarm,
    )

    with pytest.raises(
        RuntimeError,
        match="live alarm conflicts with durable alarm",
    ):
        service.recover(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            timestamp=(
                BASE_TIME + timedelta(minutes=5)
            ),
        )

    assert instance.alarms == (
        conflicting_alarm,
    )

    transitions = history.list_transitions(
        durable_alarm.alarm_id
    )

    assert len(transitions) == 1
    assert (
        transitions[0].transition_type
        is AlarmTransitionType.OPENED
    )


@pytest.mark.parametrize(
    "state",
    [
        AlarmState.RESOLVED,
        AlarmState.CLOSED,
    ],
)
def test_recover_does_not_restore_inactive_alarm_states(
    state: AlarmState,
) -> None:
    (
        _,
        _,
        node,
        instance,
        history,
        service,
    ) = make_context()

    resolved_at = (
        BASE_TIME + timedelta(minutes=2)
    )

    closed_at = (
        BASE_TIME + timedelta(minutes=3)
        if state is AlarmState.CLOSED
        else None
    )

    alarm = AlarmRecord(
        alarm_id="alarm-inactive",
        alarm_type="TEST_ALARM",
        severity=AlarmSeverity.CRITICAL,
        state=state,
        timestamp=BASE_TIME,
        source=instance.instance_id,
        title="Inactive alarm",
        description="Must not be recovered",
        resolved_at=resolved_at,
        closed_at=closed_at,
    )

    transition_type = (
        AlarmTransitionType.CLOSED
        if state is AlarmState.CLOSED
        else AlarmTransitionType.RESOLVED
    )

    transition_time = (
        closed_at
        if state is AlarmState.CLOSED
        else resolved_at
    )

    assert transition_time is not None

    transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=alarm.alarm_id,
            transition_type=transition_type,
            timestamp=transition_time,
            source=instance.instance_id,
            state=alarm.state,
        ),
        alarm_id=alarm.alarm_id,
        transition_type=transition_type,
        timestamp=transition_time,
        source=instance.instance_id,
        state=alarm.state,
    )

    history.record_lifecycle(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        alarm=alarm,
        transition=transition,
    )

    result = service.recover(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        timestamp=(
            BASE_TIME + timedelta(minutes=10)
        ),
    )

    assert result.recovered_count == 0
    assert instance.alarms == ()

    transitions = history.list_transitions(
        alarm.alarm_id
    )

    assert len(transitions) == 1
    assert (
        transitions[0].transition_type
        is transition_type
    )


def test_sqlite_recovery_survives_runtime_restart(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "noc-history.db"
    )

    # ------------------------------------------------------------
    # Runtime A
    # ------------------------------------------------------------

    database_a = SQLiteHistoryDatabase(
        database_path
    )

    history_a = SQLiteAlarmHistoryRepository(
        database_a
    )

    repository_a = InMemoryNodeRepository()
    registry_a = NodeRegistry(repository_a)

    node_a = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    instance_a = node_a.create_instance(
        instance_id="streaming-primary"
    )

    registry_a.register(node_a)

    alarm = make_alarm()

    persist_opened_alarm(
        history_a,
        node_a,
        instance_a,
        alarm,
    )

    assert history_a.get_current(
        alarm.alarm_id
    ) == alarm

    assert instance_a.alarms == ()

    # ------------------------------------------------------------
    # Simulated process restart:
    # discard every live in-memory object.
    # ------------------------------------------------------------

    del registry_a
    del repository_a
    del node_a
    del instance_a
    del history_a
    del database_a

    # ------------------------------------------------------------
    # Runtime B
    # ------------------------------------------------------------

    database_b = SQLiteHistoryDatabase(
        database_path
    )

    history_b = SQLiteAlarmHistoryRepository(
        database_b
    )

    repository_b = InMemoryNodeRepository()
    registry_b = NodeRegistry(repository_b)

    node_b = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    instance_b = node_b.create_instance(
        instance_id="streaming-primary"
    )

    registry_b.register(node_b)

    service_b = AlarmRecoveryService(
        registry=registry_b,
        history_repository=history_b,
    )

    recovered_at = (
        BASE_TIME + timedelta(minutes=15)
    )

    result = service_b.recover(
        node_id=node_b.node_id,
        instance_id=instance_b.instance_id,
        timestamp=recovered_at,
    )

    assert result.recovered_count == 1
    assert result.recovered == (alarm,)

    assert instance_b.alarms == (
        alarm,
    )

    current = history_b.get_current(
        alarm.alarm_id
    )

    assert current == alarm
    assert current.alarm_id == alarm.alarm_id
    assert current.state is AlarmState.ACTIVE

    transitions = history_b.list_transitions(
        alarm.alarm_id
    )

    assert len(transitions) == 2

    assert (
        transitions[0].transition_type
        is AlarmTransitionType.OPENED
    )

    assert (
        transitions[1].transition_type
        is AlarmTransitionType.RECOVERED_AT_STARTUP
    )

    assert (
        transitions[1].alarm_id
        == alarm.alarm_id
    )

    assert (
        transitions[1].timestamp
        == recovered_at
    )


class FailingLifecycleAlarmHistoryRepository(
    InMemoryAlarmHistoryRepository
):
    def record_lifecycle(
        self,
        *,
        node_id,
        instance_id,
        alarm,
        transition,
    ) -> None:
        if (
            transition.transition_type
            is AlarmTransitionType.RECOVERED_AT_STARTUP
        ):
            raise RuntimeError(
                "simulated recovery history failure"
            )

        super().record_lifecycle(
            node_id=node_id,
            instance_id=instance_id,
            alarm=alarm,
            transition=transition,
        )


def test_recovery_history_failure_does_not_modify_live_projection() -> None:
    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    durable_history = InMemoryAlarmHistoryRepository()

    alarm = make_alarm()

    persist_opened_alarm(
        durable_history,
        node,
        instance,
        alarm,
    )

    failing_history = FailingLifecycleAlarmHistoryRepository()

    for transition in durable_history.list_transitions(
        alarm.alarm_id
    ):
        failing_history.record_lifecycle(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            alarm=alarm,
            transition=transition,
        )

    service = AlarmRecoveryService(
        registry=registry,
        history_repository=failing_history,
    )

    assert instance.alarms == ()

    with pytest.raises(
        RuntimeError,
        match="simulated recovery history failure",
    ):
        service.recover(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            timestamp=BASE_TIME + timedelta(minutes=5),
        )

    assert instance.alarms == ()

    transitions = failing_history.list_transitions(
        alarm.alarm_id
    )

    assert len(transitions) == 1
    assert (
        transitions[0].transition_type
        is AlarmTransitionType.OPENED
    )


def test_recovery_is_scoped_to_requested_instance() -> None:
    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    target_instance = node.create_instance(
        instance_id="streaming-primary"
    )

    other_instance = node.create_instance(
        instance_id="streaming-secondary"
    )

    registry.register(node)

    history = InMemoryAlarmHistoryRepository()

    other_alarm = AlarmRecord(
        alarm_id="alarm-secondary",
        alarm_type="TEST_ALARM",
        severity=AlarmSeverity.CRITICAL,
        state=AlarmState.ACTIVE,
        timestamp=BASE_TIME,
        source=other_instance.instance_id,
        title="Secondary alarm",
        description="Alarm from another instance",
    )

    persist_opened_alarm(
        history,
        node,
        other_instance,
        other_alarm,
    )

    service = AlarmRecoveryService(
        registry=registry,
        history_repository=history,
    )

    result = service.recover(
        node_id=node.node_id,
        instance_id=target_instance.instance_id,
        timestamp=BASE_TIME + timedelta(minutes=5),
    )

    assert result.recovered_count == 0
    assert target_instance.alarms == ()
    assert other_instance.alarms == ()

    transitions = history.list_transitions(
        other_alarm.alarm_id
    )

    assert len(transitions) == 1
    assert (
        transitions[0].transition_type
        is AlarmTransitionType.OPENED
    )
