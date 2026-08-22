"""Tests for critical-path no-readers alarm coordination."""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)
from app.noc.domain.node import Node
from app.noc.domain.node_alarm import AlarmState
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import NodeRegistry
from app.noc.services.alarm_service import (
    AlarmDisposition,
    AlarmService,
)
from app.noc.services.critical_path_no_readers_alarm_service import (
    CriticalPathNoReadersAlarmResult,
    CriticalPathNoReadersAlarmService,
)
from app.noc.services.critical_path_reader_evaluator import (
    CriticalPathReaderEvaluation,
    CriticalPathReaderState,
)
from app.noc.services.critical_path_reader_stabilizer import (
    CriticalPathReaderStabilization,
)


BASE_TIME = datetime(
    2026,
    8,
    23,
    3,
    45,
    tzinfo=timezone.utc,
)


class MemoryRepository:
    def __init__(self):
        self.nodes = {}

    def save(self, node):
        self.nodes[node.node_id.id] = node

    def get(self, node_id):
        return self.nodes.get(node_id.id)

    def exists(self, node_id):
        return node_id.id in self.nodes

    def list_all(self):
        return tuple(self.nodes.values())

    def delete(self, node_id):
        return self.nodes.pop(
            node_id.id,
            None,
        ) is not None

    def count(self):
        return len(self.nodes)


def make_context():
    repository = MemoryRepository()
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

    alarm_service = AlarmService(registry)

    service = CriticalPathNoReadersAlarmService(
        alarm_service=alarm_service,
    )

    return (
        node,
        instance,
        alarm_service,
        service,
    )


def policy(
    path: str = "ejtv",
) -> CriticalPathPolicy:
    return CriticalPathPolicy(
        path=path,
        no_readers_grace_period=timedelta(
            seconds=15
        ),
    )


def build_session(
    *,
    session_id: str,
    role: SessionRole,
    path: str,
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=SessionProtocol.SRT,
        role=role,
        state=(
            "publish"
            if role is SessionRole.PUBLISHER
            else "read"
        ),
        remote_ip="201.192.154.132",
        remote_port=50000,
        path=path,
        connected_since=BASE_TIME,
    )


def stabilization(
    *,
    path: str = "ejtv",
    state: CriticalPathReaderState,
    confirmed_no_readers: bool = False,
) -> CriticalPathReaderStabilization:
    expected_policy = policy(path)

    if state is CriticalPathReaderState.NO_READERS:
        publishers = (
            build_session(
                session_id=f"publisher-{path}",
                role=SessionRole.PUBLISHER,
                path=path,
            ),
        )
        readers = ()
        no_readers_since = (
            BASE_TIME - timedelta(seconds=15)
        )

    elif state is CriticalPathReaderState.HAS_READERS:
        publishers = (
            build_session(
                session_id=f"publisher-{path}",
                role=SessionRole.PUBLISHER,
                path=path,
            ),
        )
        readers = (
            build_session(
                session_id=f"reader-{path}",
                role=SessionRole.READER,
                path=path,
            ),
        )
        no_readers_since = None
        confirmed_no_readers = False

    elif state is CriticalPathReaderState.INCONSISTENT:
        publishers = ()
        readers = (
            build_session(
                session_id=f"reader-{path}",
                role=SessionRole.READER,
                path=path,
            ),
        )
        no_readers_since = None
        confirmed_no_readers = False

    else:
        publishers = ()
        readers = ()
        no_readers_since = None
        confirmed_no_readers = False

    evaluation = CriticalPathReaderEvaluation(
        policy=expected_policy,
        state=state,
        publishers=publishers,
        readers=readers,
    )

    return CriticalPathReaderStabilization(
        evaluation=evaluation,
        observed_at=BASE_TIME,
        no_readers_since=no_readers_since,
        confirmed_no_readers=confirmed_no_readers,
    )


def test_service_requires_alarm_service() -> None:
    with pytest.raises(TypeError):
        CriticalPathNoReadersAlarmService(
            alarm_service=object(),  # type: ignore[arg-type]
        )


def test_no_readers_in_grace_period_is_noop() -> None:
    node, instance, alarm_service, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathReaderState.NO_READERS,
            confirmed_no_readers=False,
        ),
        timestamp=BASE_TIME,
    )

    assert isinstance(
        result,
        CriticalPathNoReadersAlarmResult,
    )
    assert result.alarm is None
    assert result.receipt is None

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_confirmed_no_readers_raises_alarm() -> None:
    node, instance, alarm_service, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathReaderState.NO_READERS,
            confirmed_no_readers=True,
        ),
        timestamp=BASE_TIME,
    )

    assert result.alarm is not None
    assert result.receipt is not None
    assert result.receipt.disposition is (
        AlarmDisposition.RAISED
    )
    assert result.alarm.state is AlarmState.ACTIVE
    assert result.alarm.alarm_type == (
        "CRITICAL_PATH_NO_READERS"
    )


def test_repeated_no_readers_does_not_duplicate() -> None:
    node, instance, alarm_service, service = make_context()

    condition = stabilization(
        state=CriticalPathReaderState.NO_READERS,
        confirmed_no_readers=True,
    )

    first = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=condition,
        timestamp=BASE_TIME,
    )

    second = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=condition,
        timestamp=BASE_TIME,
    )

    assert first.alarm is not None
    assert second.alarm is first.alarm
    assert second.receipt is None

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == (first.alarm,)


@pytest.mark.parametrize(
    "recovered_state",
    (
        CriticalPathReaderState.HAS_READERS,
        CriticalPathReaderState.INACTIVE,
        CriticalPathReaderState.INCONSISTENT,
    ),
)
def test_non_no_readers_resolves_active_alarm(
    recovered_state: CriticalPathReaderState,
) -> None:
    node, instance, alarm_service, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathReaderState.NO_READERS,
            confirmed_no_readers=True,
        ),
        timestamp=BASE_TIME,
    )

    assert raised.alarm is not None

    recovered = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=recovered_state,
        ),
        timestamp=BASE_TIME,
    )

    assert recovered.alarm is not None
    assert recovered.receipt is not None
    assert recovered.receipt.disposition is (
        AlarmDisposition.RESOLVED
    )
    assert recovered.alarm.state is AlarmState.RESOLVED
    assert recovered.alarm.alarm_id == (
        raised.alarm.alarm_id
    )


def test_acknowledged_alarm_resolves_on_recovery() -> None:
    node, instance, alarm_service, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathReaderState.NO_READERS,
            confirmed_no_readers=True,
        ),
        timestamp=BASE_TIME,
    )

    assert raised.alarm is not None

    acknowledged = alarm_service.acknowledge(
        node.node_id,
        instance.instance_id,
        raised.alarm.alarm_id,
        acknowledged_by="operator",
        timestamp=BASE_TIME,
    )

    assert acknowledged.alarm.state is (
        AlarmState.ACKNOWLEDGED
    )

    recovered = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathReaderState.HAS_READERS,
        ),
        timestamp=BASE_TIME,
    )

    assert recovered.alarm is not None
    assert recovered.alarm.state is AlarmState.RESOLVED
    assert recovered.alarm.acknowledged is True
    assert recovered.alarm.acknowledged_by == "operator"


def test_paths_have_independent_alarms() -> None:
    node, instance, alarm_service, service = make_context()

    first = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            path="ejtv",
            state=CriticalPathReaderState.NO_READERS,
            confirmed_no_readers=True,
        ),
        timestamp=BASE_TIME,
    )

    second = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            path="enlace",
            state=CriticalPathReaderState.NO_READERS,
            confirmed_no_readers=True,
        ),
        timestamp=BASE_TIME,
    )

    assert first.alarm is not None
    assert second.alarm is not None
    assert first.alarm.alarm_id != second.alarm.alarm_id

    active = alarm_service.active(
        node.node_id,
        instance.instance_id,
    )

    assert len(active) == 2


def test_recovery_resolves_only_matching_path() -> None:
    node, instance, alarm_service, service = make_context()

    first = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            path="ejtv",
            state=CriticalPathReaderState.NO_READERS,
            confirmed_no_readers=True,
        ),
        timestamp=BASE_TIME,
    )

    second = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            path="enlace",
            state=CriticalPathReaderState.NO_READERS,
            confirmed_no_readers=True,
        ),
        timestamp=BASE_TIME,
    )

    service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            path="ejtv",
            state=CriticalPathReaderState.HAS_READERS,
        ),
        timestamp=BASE_TIME,
    )

    assert first.alarm is not None
    assert second.alarm is not None

    active = alarm_service.active(
        node.node_id,
        instance.instance_id,
    )

    assert active == (second.alarm,)


def test_process_requires_node_id() -> None:
    _, instance, _, service = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=object(),  # type: ignore[arg-type]
            instance_id=instance.instance_id,
            stabilization=stabilization(
                state=CriticalPathReaderState.NO_READERS,
            ),
            timestamp=BASE_TIME,
        )


def test_process_requires_instance_id() -> None:
    node, _, _, service = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=node.node_id,
            instance_id="streaming-primary",  # type: ignore[arg-type]
            stabilization=stabilization(
                state=CriticalPathReaderState.NO_READERS,
            ),
            timestamp=BASE_TIME,
        )


def test_process_requires_stabilization() -> None:
    node, instance, _, service = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            stabilization=object(),  # type: ignore[arg-type]
            timestamp=BASE_TIME,
        )
