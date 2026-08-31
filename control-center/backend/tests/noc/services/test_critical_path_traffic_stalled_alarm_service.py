"""Tests for critical-path stalled-traffic alarm coordination."""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.streaming.metrics import (
    MeasurementQuality,
    StreamingPathMeasurement,
)
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
from app.noc.services.critical_path_traffic_evaluator import (
    CriticalPathTrafficEvaluation,
    CriticalPathTrafficState,
)
from app.noc.services.critical_path_traffic_stabilizer import (
    CriticalPathTrafficStabilization,
)
from app.noc.services.critical_path_traffic_stalled_alarm_service import (
    CriticalPathTrafficStalledAlarmResult,
    CriticalPathTrafficStalledAlarmService,
)


BASE_TIME = datetime(
    2026, 8, 31, 8, 30, tzinfo=timezone.utc
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

    service = CriticalPathTrafficStalledAlarmService(
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
        traffic_stalled_grace_period=timedelta(
            seconds=15
        ),
    )


def media_path(
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


def measurement(
    *,
    path: str = "ejtv",
    inbound_bitrate_bps: float = 0.0,
) -> StreamingPathMeasurement:
    return StreamingPathMeasurement(
        name=path,
        status=MediaPathStatus.ACTIVE,
        previous_status=MediaPathStatus.ACTIVE,
        reader_count=2,
        reader_delta=0,
        inbound_delta_bytes=0,
        outbound_delta_bytes=0,
        inbound_bitrate_bps=inbound_bitrate_bps,
        outbound_bitrate_bps=0.0,
        state_changed=False,
        quality=MeasurementQuality.AVAILABLE,
    )


def stabilization(
    *,
    path: str = "ejtv",
    state: CriticalPathTrafficState,
    confirmed_stalled: bool = False,
) -> CriticalPathTrafficStabilization:
    expected_policy = policy(path)

    if state is CriticalPathTrafficState.STALLED:
        current_path = media_path(path=path)
        current_measurement = measurement(path=path)
        stalled_since = (
            BASE_TIME - timedelta(seconds=15)
        )

    elif state is CriticalPathTrafficState.HEALTHY:
        current_path = media_path(path=path)
        current_measurement = measurement(
            path=path,
            inbound_bitrate_bps=4_500_000.0,
        )
        stalled_since = None
        confirmed_stalled = False

    elif state is CriticalPathTrafficState.UNKNOWN:
        current_path = media_path(path=path)
        current_measurement = None
        stalled_since = None
        confirmed_stalled = False

    else:
        current_path = None
        current_measurement = None
        stalled_since = None
        confirmed_stalled = False

    evaluation = CriticalPathTrafficEvaluation(
        policy=expected_policy,
        state=state,
        media_path=current_path,
        measurement=current_measurement,
    )

    return CriticalPathTrafficStabilization(
        evaluation=evaluation,
        observed_at=BASE_TIME,
        stalled_since=stalled_since,
        confirmed_stalled=confirmed_stalled,
    )


def test_service_requires_alarm_service() -> None:
    with pytest.raises(TypeError):
        CriticalPathTrafficStalledAlarmService(
            alarm_service=object(),  # type: ignore[arg-type]
        )


def test_stalled_in_grace_period_is_noop() -> None:
    node, instance, alarm_service, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathTrafficState.STALLED,
            confirmed_stalled=False,
        ),
        timestamp=BASE_TIME,
    )

    assert isinstance(
        result,
        CriticalPathTrafficStalledAlarmResult,
    )
    assert result.alarm is None
    assert result.receipt is None

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_confirmed_stalled_raises_alarm() -> None:
    node, instance, _, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathTrafficState.STALLED,
            confirmed_stalled=True,
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
        == "CRITICAL_PATH_TRAFFIC_STALLED"
    )


def test_repeated_stalled_does_not_duplicate() -> None:
    node, instance, alarm_service, service = make_context()

    condition = stabilization(
        state=CriticalPathTrafficState.STALLED,
        confirmed_stalled=True,
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


def test_healthy_resolves_active_alarm() -> None:
    node, instance, _, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathTrafficState.STALLED,
            confirmed_stalled=True,
        ),
        timestamp=BASE_TIME,
    )

    assert raised.alarm is not None

    recovered = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathTrafficState.HEALTHY,
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


@pytest.mark.parametrize(
    "state",
    (
        CriticalPathTrafficState.UNKNOWN,
        CriticalPathTrafficState.INACTIVE,
    ),
)
def test_unknown_or_inactive_preserves_active_alarm(
    state: CriticalPathTrafficState,
) -> None:
    node, instance, _, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathTrafficState.STALLED,
            confirmed_stalled=True,
        ),
        timestamp=BASE_TIME,
    )

    assert raised.alarm is not None

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=state,
        ),
        timestamp=BASE_TIME,
    )

    assert result.alarm is raised.alarm
    assert result.receipt is None
    assert result.alarm.state is AlarmState.ACTIVE


def test_acknowledged_alarm_resolves_on_healthy() -> None:
    node, instance, alarm_service, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization(
            state=CriticalPathTrafficState.STALLED,
            confirmed_stalled=True,
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
            state=CriticalPathTrafficState.HEALTHY,
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
