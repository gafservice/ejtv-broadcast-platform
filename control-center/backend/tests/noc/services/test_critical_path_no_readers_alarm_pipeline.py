"""End-to-end critical-path no-readers alarm pipeline tests."""

from datetime import datetime, timedelta, timezone

from app.domain.streaming.models import (
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaReader,
    MediaSource,
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
    CriticalPathNoReadersAlarmService,
)
from app.noc.services.critical_path_reader_evaluator import (
    CriticalPathReaderEvaluator,
    CriticalPathReaderState,
)
from app.noc.services.critical_path_reader_stabilizer import (
    CriticalPathReaderStabilizer,
)


BASE_TIME = datetime(
    2026,
    8,
    23,
    4,
    0,
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

    return (
        node,
        instance,
        alarm_service,
        CriticalPathReaderEvaluator(),
        CriticalPathReaderStabilizer(),
        CriticalPathNoReadersAlarmService(
            alarm_service=alarm_service,
        ),
    )


def build_policy() -> CriticalPathPolicy:
    return CriticalPathPolicy(
        path="ejtv",
        no_readers_grace_period=timedelta(
            seconds=15
        ),
    )


def build_media_path(
    *,
    reader_count: int,
) -> MediaPath:
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
        readers=tuple(
            MediaReader(
                reader_type="srtConn",
                reader_id=f"reader-{index}",
            )
            for index in range(reader_count)
        ),
    )


def build_snapshot(
    *,
    captured_at: datetime,
    reader_count: int,
) -> MediaMTXSnapshot:
    media_path = build_media_path(
        reader_count=reader_count,
    )

    return MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(media_path,),
        reported_item_count=1,
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
    reader_count,
):
    snapshot = build_snapshot(
        captured_at=timestamp,
        reader_count=reader_count,
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


def test_critical_path_no_readers_full_lifecycle() -> None:
    (
        node,
        instance,
        alarm_service,
        evaluator,
        stabilizer,
        alarm_coordinator,
    ) = make_context()

    policy = build_policy()

    # t=0:
    # MediaMTX reports the ejtv path ACTIVE with an
    # mpegtsSource, but there are no readers.
    evaluation_0, stabilization_0, result_0 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME,
        reader_count=0,
    )

    assert (
        evaluation_0.state
        is CriticalPathReaderState.NO_READERS
    )
    assert evaluation_0.media_path is not None
    assert (
        evaluation_0.media_path.source is not None
    )
    assert (
        evaluation_0.media_path.source.source_type
        == "mpegtsSource"
    )
    assert evaluation_0.media_path.reader_count == 0

    assert stabilization_0.confirmed_no_readers is False
    assert stabilization_0.no_readers_since == BASE_TIME
    assert result_0.alarm is None
    assert result_0.receipt is None

    # t=14: still inside grace period.
    _, stabilization_14, result_14 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=14),
        reader_count=0,
    )

    assert stabilization_14.confirmed_no_readers is False
    assert result_14.alarm is None
    assert result_14.receipt is None

    # t=15: condition becomes confirmed.
    _, stabilization_15, result_15 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=15),
        reader_count=0,
    )

    assert stabilization_15.confirmed_no_readers is True
    assert result_15.alarm is not None
    assert result_15.receipt is not None

    assert result_15.receipt.disposition is (
        AlarmDisposition.RAISED
    )
    assert result_15.alarm.state is AlarmState.ACTIVE

    assert (
        result_15.alarm.attributes["source_type"]
        == "mpegtsSource"
    )
    assert (
        result_15.alarm.attributes["reader_count"]
        == "0"
    )

    raised_alarm_id = result_15.alarm.alarm_id

    # t=30: still no readers; no duplicate alarm.
    _, stabilization_30, result_30 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=30),
        reader_count=0,
    )

    assert stabilization_30.confirmed_no_readers is True
    assert result_30.alarm is not None
    assert result_30.alarm.alarm_id == raised_alarm_id
    assert result_30.receipt is None

    active = alarm_service.active(
        node.node_id,
        instance.instance_id,
    )

    assert len(active) == 1
    assert active[0].alarm_id == raised_alarm_id

    # t=45:
    # The same MediaMTX path now reports one reader.
    evaluation_45, stabilization_45, result_45 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=45),
        reader_count=1,
    )

    assert (
        evaluation_45.state
        is CriticalPathReaderState.HAS_READERS
    )
    assert evaluation_45.media_path is not None
    assert evaluation_45.media_path.reader_count == 1

    assert stabilization_45.no_readers_since is None
    assert stabilization_45.confirmed_no_readers is False

    assert result_45.alarm is not None
    assert result_45.receipt is not None

    assert result_45.receipt.disposition is (
        AlarmDisposition.RESOLVED
    )
    assert result_45.alarm.state is AlarmState.RESOLVED
    assert result_45.alarm.alarm_id == raised_alarm_id

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()
