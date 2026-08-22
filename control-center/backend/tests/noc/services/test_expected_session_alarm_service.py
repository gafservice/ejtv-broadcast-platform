"""Tests for expected multimedia session alarm coordination."""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.expected_session_policy import (
    ExpectedSessionPolicy,
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
from app.noc.services.expected_session_alarm_service import (
    ExpectedSessionAlarmResult,
    ExpectedSessionAlarmService,
)
from app.noc.services.expected_session_evaluator import (
    ExpectedSessionEvaluation,
    ExpectedSessionState,
)
from app.noc.services.expected_session_stabilizer import (
    ExpectedSessionStabilization,
)


BASE_TIME = datetime(
    2026,
    8,
    23,
    0,
    15,
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

    service = ExpectedSessionAlarmService(
        alarm_service=alarm_service,
    )

    return (
        node,
        instance,
        alarm_service,
        service,
    )


def policy(
    policy_id: str = "ejtv-srt-reader",
    path: str = "ejtv",
) -> ExpectedSessionPolicy:
    return ExpectedSessionPolicy(
        policy_id=policy_id,
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        path=path,
        missing_grace_period=timedelta(
            seconds=15
        ),
    )


def session(
    path: str = "ejtv",
) -> ActiveSession:
    return ActiveSession(
        session_id=f"session-{path}",
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        state="read",
        remote_ip="201.192.154.132",
        remote_port=50000,
        path=path,
        connected_since=BASE_TIME,
    )


def stabilization(
    *,
    expected_policy: ExpectedSessionPolicy | None = None,
    state: ExpectedSessionState,
    confirmed_missing: bool = False,
    observed_at: datetime = BASE_TIME,
) -> ExpectedSessionStabilization:
    expected_policy = expected_policy or policy()

    if state is ExpectedSessionState.PRESENT:
        matching_sessions = (
            session(
                expected_policy.path or "ejtv"
            ),
        )
        missing_since = None
        confirmed_missing = False
    else:
        matching_sessions = ()
        missing_since = (
            observed_at - timedelta(seconds=15)
        )

    evaluation = ExpectedSessionEvaluation(
        policy=expected_policy,
        state=state,
        matching_sessions=matching_sessions,
    )

    return ExpectedSessionStabilization(
        evaluation=evaluation,
        observed_at=observed_at,
        missing_since=missing_since,
        confirmed_missing=confirmed_missing,
    )


def test_service_requires_alarm_service() -> None:
    with pytest.raises(TypeError):
        ExpectedSessionAlarmService(
            alarm_service=object(),  # type: ignore[arg-type]
        )


def test_present_without_alarm_is_noop() -> None:
    node, instance, alarm_service, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=ExpectedSessionState.PRESENT,
        ),
        timestamp=BASE_TIME,
    )

    assert isinstance(
        result,
        ExpectedSessionAlarmResult,
    )
    assert result.alarm is None
    assert result.receipt is None

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_missing_during_grace_period_is_noop() -> None:
    node, instance, alarm_service, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=ExpectedSessionState.MISSING,
            confirmed_missing=False,
        ),
        timestamp=BASE_TIME,
    )

    assert result.alarm is None
    assert result.receipt is None

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_confirmed_missing_raises_alarm() -> None:
    node, instance, alarm_service, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=ExpectedSessionState.MISSING,
            confirmed_missing=True,
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
        "EXPECTED_SESSION_MISSING"
    )
    assert (
        result.alarm.attributes["policy_id"]
        == "ejtv-srt-reader"
    )


def test_confirmed_missing_does_not_duplicate_alarm() -> None:
    node, instance, alarm_service, service = make_context()

    missing = stabilization(
        state=ExpectedSessionState.MISSING,
        confirmed_missing=True,
    )

    first = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=missing,
        timestamp=BASE_TIME,
    )

    second = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=missing,
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert first.alarm is not None
    assert second.alarm is first.alarm
    assert second.receipt is None

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == (first.alarm,)


def test_present_resolves_active_alarm() -> None:
    node, instance, alarm_service, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=ExpectedSessionState.MISSING,
            confirmed_missing=True,
        ),
        timestamp=BASE_TIME,
    )

    assert raised.alarm is not None

    recovered = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=ExpectedSessionState.PRESENT,
            observed_at=BASE_TIME + timedelta(seconds=10),
        ),
        timestamp=BASE_TIME + timedelta(seconds=10),
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

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_acknowledged_alarm_resolves_on_recovery() -> None:
    node, instance, alarm_service, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=ExpectedSessionState.MISSING,
            confirmed_missing=True,
        ),
        timestamp=BASE_TIME,
    )

    assert raised.alarm is not None

    acknowledged = alarm_service.acknowledge(
        node.node_id,
        instance.instance_id,
        raised.alarm.alarm_id,
        acknowledged_by="operator",
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    assert acknowledged.alarm.state is (
        AlarmState.ACKNOWLEDGED
    )

    recovered = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=ExpectedSessionState.PRESENT,
            observed_at=BASE_TIME + timedelta(seconds=10),
        ),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert recovered.alarm is not None
    assert recovered.alarm.state is AlarmState.RESOLVED
    assert recovered.alarm.acknowledged is True
    assert recovered.alarm.acknowledged_by == "operator"


def test_policy_ids_have_independent_alarms() -> None:
    node, instance, alarm_service, service = make_context()

    first_policy = policy(
        policy_id="directv",
        path="directv",
    )

    second_policy = policy(
        policy_id="nossa",
        path="nossa",
    )

    first = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            expected_policy=first_policy,
            state=ExpectedSessionState.MISSING,
            confirmed_missing=True,
        ),
        timestamp=BASE_TIME,
    )

    second = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            expected_policy=second_policy,
            state=ExpectedSessionState.MISSING,
            confirmed_missing=True,
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

    assert {
        alarm.attributes["policy_id"]
        for alarm in active
    } == {
        "directv",
        "nossa",
    }


def test_recovery_resolves_only_matching_policy_alarm() -> None:
    node, instance, alarm_service, service = make_context()

    first_policy = policy(
        policy_id="directv",
        path="directv",
    )

    second_policy = policy(
        policy_id="nossa",
        path="nossa",
    )

    first = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            expected_policy=first_policy,
            state=ExpectedSessionState.MISSING,
            confirmed_missing=True,
        ),
        timestamp=BASE_TIME,
    )

    second = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            expected_policy=second_policy,
            state=ExpectedSessionState.MISSING,
            confirmed_missing=True,
        ),
        timestamp=BASE_TIME,
    )

    service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            expected_policy=first_policy,
            state=ExpectedSessionState.PRESENT,
            observed_at=BASE_TIME + timedelta(seconds=10),
        ),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    active = alarm_service.active(
        node.node_id,
        instance.instance_id,
    )

    assert first.alarm is not None
    assert second.alarm is not None

    assert active == (second.alarm,)


def test_process_requires_node_id() -> None:
    _, instance, _, service = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=object(),  # type: ignore[arg-type]
            instance_id=instance.instance_id,
            stabilization=stabilization(
                state=ExpectedSessionState.MISSING,
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
                state=ExpectedSessionState.MISSING,
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


def test_timestamp_must_be_utc() -> None:
    node, instance, _, service = make_context()

    non_utc = datetime(
        2026,
        8,
        23,
        1,
        15,
        tzinfo=timezone(timedelta(hours=1)),
    )

    with pytest.raises(
        ValueError,
        match="timestamp must be expressed in UTC",
    ):
        service.process(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            stabilization=stabilization(
                state=ExpectedSessionState.MISSING,
            ),
            timestamp=non_utc,
        )
