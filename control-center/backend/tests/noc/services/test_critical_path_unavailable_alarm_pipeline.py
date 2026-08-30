"""End-to-end critical-path unavailable alarm pipeline tests."""

from datetime import datetime, timedelta, timezone

from app.domain.streaming.models import (
    MediaMTXSnapshot,
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
    CriticalPathAvailabilityEvaluator,
    CriticalPathAvailabilityState,
)
from app.noc.services.critical_path_availability_stabilizer import (
    CriticalPathAvailabilityStabilizer,
)
from app.noc.services.critical_path_unavailable_alarm_service import (
    CriticalPathUnavailableAlarmService,
)


BASE_TIME = datetime(
    2026, 8, 30, 5, 0, tzinfo=timezone.utc
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

    return (
        node,
        instance,
        alarm_service,
        CriticalPathAvailabilityEvaluator(),
        CriticalPathAvailabilityStabilizer(),
        CriticalPathUnavailableAlarmService(
            alarm_service=alarm_service,
        ),
    )


def build_policy() -> CriticalPathPolicy:
    return CriticalPathPolicy(
        path="ejtv",
        unavailable_grace_period=timedelta(
            seconds=15
        ),
    )


def build_available_path() -> MediaPath:
    return MediaPath(
        name="ejtv",
        configuration_name="ejtv",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(
            source_type="mpegtsSource",
        ),
    )


def build_snapshot(
    *,
    captured_at: datetime,
    available: bool,
) -> MediaMTXSnapshot:
    paths = (
        (build_available_path(),)
        if available
        else ()
    )

    return MediaMTXSnapshot(
        captured_at=captured_at,
        paths=paths,
        reported_item_count=len(paths),
        reported_page_count=1,
    )


def process_cycle(
    *,
    evaluator,
    stabilizer,
    alarm_coordinator,
    node,
    instance,
    policy,
    timestamp,
    available,
):
    snapshot = build_snapshot(
        captured_at=timestamp,
        available=available,
    )

    evaluations = evaluator.evaluate(
        snapshot=snapshot,
        policies=(policy,),
    )

    assert len(evaluations) == 1

    stabilization = stabilizer.stabilize(
        evaluation=evaluations[0],
        observed_at=timestamp,
    )

    alarm_result = alarm_coordinator.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization,
        timestamp=timestamp,
    )

    return (
        evaluations[0],
        stabilization,
        alarm_result,
    )


def test_critical_path_unavailable_full_lifecycle() -> None:
    (
        node,
        instance,
        alarm_service,
        evaluator,
        stabilizer,
        alarm_coordinator,
    ) = make_context()

    policy = build_policy()

    # t=0: path is healthy and available.
    evaluation_0, stabilization_0, result_0 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME,
        available=True,
    )

    assert (
        evaluation_0.state
        is CriticalPathAvailabilityState.AVAILABLE
    )
    assert evaluation_0.media_path is not None
    assert stabilization_0.unavailable_since is None
    assert stabilization_0.confirmed_unavailable is False
    assert result_0.alarm is None
    assert result_0.receipt is None

    # t=5: path disappears. Grace period begins.
    evaluation_5, stabilization_5, result_5 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=5),
        available=False,
    )

    assert (
        evaluation_5.state
        is CriticalPathAvailabilityState.UNAVAILABLE
    )
    assert evaluation_5.media_path is None
    assert (
        stabilization_5.unavailable_since
        == BASE_TIME + timedelta(seconds=5)
    )
    assert stabilization_5.confirmed_unavailable is False
    assert result_5.alarm is None

    # t=19: still inside grace period.
    _, stabilization_19, result_19 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=19),
        available=False,
    )

    assert stabilization_19.confirmed_unavailable is False
    assert result_19.alarm is None

    # t=20: 15 continuous seconds unavailable -> alarm.
    _, stabilization_20, result_20 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=20),
        available=False,
    )

    assert stabilization_20.confirmed_unavailable is True
    assert result_20.alarm is not None
    assert result_20.receipt is not None

    assert (
        result_20.receipt.disposition
        is AlarmDisposition.RAISED
    )
    assert result_20.alarm.state is AlarmState.ACTIVE
    assert (
        result_20.alarm.alarm_type
        == "CRITICAL_PATH_UNAVAILABLE"
    )

    assert (
        result_20.alarm.attributes["path"]
        == "ejtv"
    )
    assert (
        result_20.alarm.attributes["path_present"]
        == "false"
    )
    assert (
        result_20.alarm.attributes["status"]
        == "MISSING"
    )

    raised_alarm_id = result_20.alarm.alarm_id

    # t=30: remains unavailable; no duplicate.
    _, stabilization_30, result_30 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=30),
        available=False,
    )

    assert stabilization_30.confirmed_unavailable is True
    assert result_30.alarm is not None
    assert result_30.receipt is None
    assert (
        result_30.alarm.alarm_id
        == raised_alarm_id
    )

    active = alarm_service.active(
        node.node_id,
        instance.instance_id,
    )

    assert len(active) == 1

    # t=35: path returns; active alarm resolves.
    evaluation_35, stabilization_35, result_35 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=35),
        available=True,
    )

    assert (
        evaluation_35.state
        is CriticalPathAvailabilityState.AVAILABLE
    )
    assert stabilization_35.unavailable_since is None
    assert stabilization_35.confirmed_unavailable is False

    assert result_35.alarm is not None
    assert result_35.receipt is not None
    assert (
        result_35.receipt.disposition
        is AlarmDisposition.RESOLVED
    )
    assert result_35.alarm.state is AlarmState.RESOLVED
    assert (
        result_35.alarm.alarm_id
        == raised_alarm_id
    )

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()
