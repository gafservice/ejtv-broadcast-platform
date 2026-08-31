"""End-to-end critical-path stalled-traffic alarm pipeline tests."""

from datetime import datetime, timedelta, timezone

from app.domain.streaming.metrics import (
    MeasurementQuality,
    StreamingMeasurement,
    StreamingPathMeasurement,
)
from app.domain.streaming.models import (
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
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
from app.noc.services.critical_path_traffic_evaluator import (
    CriticalPathTrafficEvaluator,
    CriticalPathTrafficState,
)
from app.noc.services.critical_path_traffic_stabilizer import (
    CriticalPathTrafficStabilizer,
)
from app.noc.services.critical_path_traffic_stalled_alarm_service import (
    CriticalPathTrafficStalledAlarmService,
)


BASE_TIME = datetime(
    2026,
    8,
    31,
    9,
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
        CriticalPathTrafficEvaluator(),
        CriticalPathTrafficStabilizer(),
        CriticalPathTrafficStalledAlarmService(
            alarm_service=alarm_service,
        ),
    )


def build_policy() -> CriticalPathPolicy:
    return CriticalPathPolicy(
        path="ejtv",
        traffic_stalled_grace_period=timedelta(
            seconds=15
        ),
    )


def build_media_path() -> MediaPath:
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
) -> MediaMTXSnapshot:
    media_path = build_media_path()

    return MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(media_path,),
        reported_item_count=1,
        reported_page_count=1,
    )


def build_measurement(
    *,
    captured_at: datetime,
    inbound_bitrate_bps: float,
) -> StreamingMeasurement:
    previous_captured_at = (
        captured_at - timedelta(seconds=1)
    )

    path_measurement = StreamingPathMeasurement(
        name="ejtv",
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

    return StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=previous_captured_at,
        interval_seconds=1.0,
        paths=(path_measurement,),
        total_inbound_bitrate_bps=inbound_bitrate_bps,
        total_outbound_bitrate_bps=0.0,
        quality=MeasurementQuality.AVAILABLE,
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
    inbound_bitrate_bps,
):
    snapshot = build_snapshot(
        captured_at=timestamp,
    )

    traffic_measurement = build_measurement(
        captured_at=timestamp,
        inbound_bitrate_bps=inbound_bitrate_bps,
    )

    evaluations = evaluator.evaluate(
        snapshot=snapshot,
        measurement=traffic_measurement,
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


def test_critical_path_traffic_stalled_full_lifecycle() -> None:
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
    # Critical path is operational and inbound traffic is flowing.
    evaluation_0, stabilization_0, result_0 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME,
        inbound_bitrate_bps=4_500_000.0,
    )

    assert (
        evaluation_0.state
        is CriticalPathTrafficState.HEALTHY
    )
    assert evaluation_0.media_path is not None
    assert evaluation_0.measurement is not None
    assert (
        evaluation_0.measurement.inbound_bitrate_bps
        == 4_500_000.0
    )

    assert stabilization_0.stalled_since is None
    assert stabilization_0.confirmed_stalled is False
    assert result_0.alarm is None
    assert result_0.receipt is None

    # t=5:
    # Path remains operational but inbound traffic stops.
    evaluation_5, stabilization_5, result_5 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=5),
        inbound_bitrate_bps=0.0,
    )

    assert (
        evaluation_5.state
        is CriticalPathTrafficState.STALLED
    )
    assert (
        stabilization_5.stalled_since
        == BASE_TIME + timedelta(seconds=5)
    )
    assert stabilization_5.confirmed_stalled is False
    assert result_5.alarm is None
    assert result_5.receipt is None

    # t=19:
    # Still stalled, but only 14 continuous seconds.
    _, stabilization_19, result_19 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=19),
        inbound_bitrate_bps=0.0,
    )

    assert stabilization_19.confirmed_stalled is False
    assert result_19.alarm is None

    # t=20:
    # 15 continuous seconds stalled -> alarm.
    _, stabilization_20, result_20 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=20),
        inbound_bitrate_bps=0.0,
    )

    assert stabilization_20.confirmed_stalled is True
    assert result_20.alarm is not None
    assert result_20.receipt is not None

    assert (
        result_20.receipt.disposition
        is AlarmDisposition.RAISED
    )

    assert result_20.alarm.state is AlarmState.ACTIVE

    assert (
        result_20.alarm.alarm_type
        == "CRITICAL_PATH_TRAFFIC_STALLED"
    )

    assert (
        result_20.alarm.attributes["path"]
        == "ejtv"
    )

    assert (
        result_20.alarm.attributes[
            "inbound_bitrate_bps"
        ]
        == "0.0"
    )

    assert (
        result_20.alarm.attributes[
            "measurement_quality"
        ]
        == "AVAILABLE"
    )

    raised_alarm_id = result_20.alarm.alarm_id

    # t=30:
    # Still stalled -> preserve the same alarm.
    _, stabilization_30, result_30 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=30),
        inbound_bitrate_bps=0.0,
    )

    assert stabilization_30.confirmed_stalled is True
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
    assert active[0].alarm_id == raised_alarm_id

    # t=35:
    # Inbound traffic returns -> same alarm resolves.
    evaluation_35, stabilization_35, result_35 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_coordinator=alarm_coordinator,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=35),
        inbound_bitrate_bps=4_600_000.0,
    )

    assert (
        evaluation_35.state
        is CriticalPathTrafficState.HEALTHY
    )

    assert stabilization_35.stalled_since is None
    assert stabilization_35.confirmed_stalled is False

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
