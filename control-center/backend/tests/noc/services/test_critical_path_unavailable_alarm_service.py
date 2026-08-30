"""Tests for critical-path unavailable alarm coordination."""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.streaming.models import (
    MediaPath,
    MediaPathStatus,
    MediaSource,
)
from app.noc.domain.critical_path_policy import CriticalPathPolicy
from app.noc.domain.node import Node
from app.noc.domain.node_alarm import AlarmState
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import NodeRegistry
from app.noc.services.alarm_service import (
    AlarmDisposition,
    AlarmService,
)
from app.noc.services.critical_path_availability_evaluator import (
    CriticalPathAvailabilityEvaluation,
    CriticalPathAvailabilityState,
)
from app.noc.services.critical_path_availability_stabilizer import (
    CriticalPathAvailabilityStabilization,
)
from app.noc.services.critical_path_unavailable_alarm_service import (
    CriticalPathUnavailableAlarmResult,
    CriticalPathUnavailableAlarmService,
)


BASE_TIME = datetime(
    2026, 8, 30, 4, 45, tzinfo=timezone.utc
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

    service = CriticalPathUnavailableAlarmService(
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
        unavailable_grace_period=timedelta(
            seconds=15
        ),
    )


def available_media_path(
    *,
    path: str = "ejtv",
) -> MediaPath:
    return MediaPath(
        name=path,
        configuration_name=path,
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(
            source_type="mpegtsSource",
        ),
    )


def stabilization(
    *,
    path: str = "ejtv",
    state: CriticalPathAvailabilityState,
    confirmed_unavailable: bool = False,
) -> CriticalPathAvailabilityStabilization:
    expected_policy = policy(path)

    if state is CriticalPathAvailabilityState.AVAILABLE:
        media_path = available_media_path(
            path=path
        )
        unavailable_since = None
        confirmed_unavailable = False
    else:
        media_path = None
        unavailable_since = (
            BASE_TIME - timedelta(seconds=15)
        )

    evaluation = CriticalPathAvailabilityEvaluation(
        policy=expected_policy,
        state=state,
        media_path=media_path,
    )

    return CriticalPathAvailabilityStabilization(
        evaluation=evaluation,
        observed_at=BASE_TIME,
        unavailable_since=unavailable_since,
        confirmed_unavailable=confirmed_unavailable,
    )


def test_service_requires_alarm_service() -> None:
    with pytest.raises(TypeError):
        CriticalPathUnavailableAlarmService(
            alarm_service=object(),  # type: ignore[arg-type]
        )


def test_unavailable_in_grace_period_is_noop() -> None:
    node, instance, alarm_service, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathAvailabilityState.UNAVAILABLE,
            confirmed_unavailable=False,
        ),
        timestamp=BASE_TIME,
    )

    assert isinstance(
        result,
        CriticalPathUnavailableAlarmResult,
    )
    assert result.alarm is None
    assert result.receipt is None

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_confirmed_unavailable_raises_alarm() -> None:
    node, instance, _, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathAvailabilityState.UNAVAILABLE,
            confirmed_unavailable=True,
        ),
        timestamp=BASE_TIME,
    )

    assert result.alarm is not None
    assert result.receipt is not None
    assert (
        result.receipt.disposition
        is AlarmDisposition.RAISED
    )
    assert result.alarm.state is AlarmState.ACTIVE
    assert (
        result.alarm.alarm_type
        == "CRITICAL_PATH_UNAVAILABLE"
    )


def test_repeated_unavailable_does_not_duplicate() -> None:
    node, instance, alarm_service, service = make_context()

    condition = stabilization(
        state=CriticalPathAvailabilityState.UNAVAILABLE,
        confirmed_unavailable=True,
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


def test_available_resolves_active_alarm() -> None:
    node, instance, _, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathAvailabilityState.UNAVAILABLE,
            confirmed_unavailable=True,
        ),
        timestamp=BASE_TIME,
    )

    assert raised.alarm is not None

    recovered = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathAvailabilityState.AVAILABLE,
        ),
        timestamp=BASE_TIME,
    )

    assert recovered.alarm is not None
    assert recovered.receipt is not None
    assert (
        recovered.receipt.disposition
        is AlarmDisposition.RESOLVED
    )
    assert recovered.alarm.state is AlarmState.RESOLVED
    assert (
        recovered.alarm.alarm_id
        == raised.alarm.alarm_id
    )


def test_acknowledged_alarm_resolves_on_recovery() -> None:
    node, instance, alarm_service, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathAvailabilityState.UNAVAILABLE,
            confirmed_unavailable=True,
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

    assert (
        acknowledged.alarm.state
        is AlarmState.ACKNOWLEDGED
    )

    recovered = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathAvailabilityState.AVAILABLE,
        ),
        timestamp=BASE_TIME,
    )

    assert recovered.alarm is not None
    assert recovered.alarm.state is AlarmState.RESOLVED
    assert recovered.alarm.acknowledged is True
    assert (
        recovered.alarm.acknowledged_by
        == "operator"
    )
