"""Tests for SnapshotService.

ENG-013B — Node SDK
NCS reference: 20-NODE-SNAPSHOT.md
"""

from datetime import datetime, timezone

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_alarm import NodeAlarm
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_heartbeat import (
    HeartbeatRecord,
    NodeHeartbeat,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_metric import (
    MetricSample,
    NodeMetric,
)
from app.noc.domain.node_snapshot import NodeSnapshot
from app.noc.domain.node_status import (
    NodeStatus,
    NodeStatusState,
)
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import (
    NodeNotFoundError,
    NodeRegistry,
)
from app.noc.services.heartbeat_service import (
    NodeInstanceNotFoundError,
)
from app.noc.services.snapshot_service import (
    SnapshotService,
    SnapshotServiceError,
)


class MemoryRepository:
    def __init__(self) -> None:
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


TIMESTAMP = datetime(
    2026,
    8,
    13,
    20,
    0,
    tzinfo=timezone.utc,
)


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

    service = SnapshotService(
        registry
    )

    return (
        registry,
        node,
        instance,
        service,
    )


def test_service_requires_registry() -> None:
    with pytest.raises(TypeError):
        SnapshotService(
            object()  # type: ignore[arg-type]
        )


def test_build_minimal_snapshot() -> None:
    _, node, instance, service = (
        make_context()
    )

    snapshot = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    assert isinstance(
        snapshot,
        NodeSnapshot,
    )

    assert snapshot.node_id == (
        node.node_id
    )

    assert snapshot.instance_id == (
        instance.instance_id
    )

    assert snapshot.snapshot_timestamp == (
        TIMESTAMP
    )


def test_minimal_snapshot_has_no_invented_components() -> None:
    _, node, instance, service = (
        make_context()
    )

    snapshot = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    assert snapshot.status is None
    assert snapshot.health is None
    assert snapshot.metric is None
    assert snapshot.alarms is None
    assert snapshot.heartbeat is None


def test_build_uses_current_status_and_health() -> None:
    _, node, instance, service = (
        make_context()
    )

    instance.status = NodeStatus(
        NodeStatusState.RUNNING
    )

    instance.health = NodeHealth(
        NodeHealthState.HEALTHY
    )

    snapshot = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    assert snapshot.status is (
        instance.status
    )

    assert snapshot.health is (
        instance.health
    )


def test_build_uses_metrics_tuple_wrapper() -> None:
    _, node, instance, service = (
        make_context()
    )

    metrics = NodeMetric(
        samples=(
            MetricSample(
                metric="cpu_usage",
                value=42.5,
                unit="%",
                timestamp=TIMESTAMP,
            ),
        )
    )

    instance.metrics = (
        metrics,
    )

    snapshot = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    assert snapshot.metric == metrics
    assert snapshot.metric is not metrics


def test_build_uses_alarm_tuple_wrapper() -> None:
    _, node, instance, service = (
        make_context()
    )

    alarms = NodeAlarm()

    instance.alarms = (
        alarms,
    )

    snapshot = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    assert snapshot.alarms is None


def test_build_uses_heartbeat() -> None:
    _, node, instance, service = (
        make_context()
    )

    heartbeat = NodeHeartbeat(
        latest=HeartbeatRecord(
            heartbeat_id="hb-001",
            instance_id=instance.instance_id,
            sequence=1,
            timestamp=TIMESTAMP,
            contract_version="1.0.0",
            uptime=100,
        )
    )

    instance.heartbeat = heartbeat

    snapshot = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    assert snapshot.heartbeat is (
        heartbeat
    )


def test_build_stores_latest_snapshot_on_instance() -> None:
    _, node, instance, service = (
        make_context()
    )

    snapshot = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    assert instance.snapshot is (
        snapshot
    )

    assert service.latest(
        node.node_id,
        instance.instance_id,
    ) is snapshot


def test_latest_before_build_returns_none() -> None:
    _, node, instance, service = (
        make_context()
    )

    assert service.latest(
        node.node_id,
        instance.instance_id,
    ) is None


def test_unknown_node_raises() -> None:
    _, _, instance, service = (
        make_context()
    )

    unknown = NodeId.create(
        id="unknown-node",
        name="unknown",
        display_name="Unknown",
    )

    with pytest.raises(
        NodeNotFoundError
    ):
        service.build(
            unknown,
            instance.instance_id,
            timestamp=TIMESTAMP,
        )


def test_unknown_instance_raises() -> None:
    _, node, _, service = (
        make_context()
    )

    with pytest.raises(
        NodeInstanceNotFoundError
    ):
        service.build(
            node.node_id,
            NodeInstanceId(
                "streaming-backup"
            ),
            timestamp=TIMESTAMP,
        )


def test_non_utc_timestamp_rejected() -> None:
    _, node, instance, service = (
        make_context()
    )

    with pytest.raises(ValueError):
        service.build(
            node.node_id,
            instance.instance_id,
            timestamp=datetime(
                2026,
                8,
                13,
                14,
                0,
            ),
        )


def test_invalid_metric_shape_rejected() -> None:
    _, node, instance, service = (
        make_context()
    )

    instance.metrics = (
        "invalid",
    )

    with pytest.raises(
        SnapshotServiceError
    ):
        service.build(
            node.node_id,
            instance.instance_id,
            timestamp=TIMESTAMP,
        )


def test_invalid_alarm_shape_rejected() -> None:
    _, node, instance, service = (
        make_context()
    )

    instance.alarms = (
        "invalid",
    )

    with pytest.raises(
        SnapshotServiceError
    ):
        service.build(
            node.node_id,
            instance.instance_id,
            timestamp=TIMESTAMP,
        )


def test_build_does_not_modify_status_or_health() -> None:
    _, node, instance, service = (
        make_context()
    )

    status = NodeStatus(
        NodeStatusState.RUNNING
    )

    health = NodeHealth(
        NodeHealthState.HEALTHY
    )

    instance.status = status
    instance.health = health

    service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    assert instance.status is status
    assert instance.health is health


def test_repeated_build_replaces_only_snapshot() -> None:
    _, node, instance, service = (
        make_context()
    )

    first = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    later = datetime(
        2026,
        8,
        13,
        20,
        1,
        tzinfo=timezone.utc,
    )

    second = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=later,
    )

    assert first is not second
    assert instance.snapshot is second
    assert second.snapshot_timestamp == later


def test_minimal_snapshot_is_contract_valid() -> None:
    _, node, instance, service = (
        make_context()
    )

    snapshot = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    result = service.validator.validate_snapshot(
        snapshot
    )

    assert result.is_valid is True


def test_empty_capabilities_are_omitted() -> None:
    _, node, instance, service = make_context()

    assert instance.capabilities == ()

    snapshot = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    assert snapshot.capability is None


def test_empty_metrics_are_omitted() -> None:
    _, node, instance, service = make_context()

    assert instance.metrics == ()

    snapshot = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    assert snapshot.metric is None


def test_empty_alarms_are_omitted() -> None:
    _, node, instance, service = make_context()

    assert instance.alarms == ()

    snapshot = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    assert snapshot.alarms is None


def test_metric_sample_collection_is_composed() -> None:
    _, node, instance, service = make_context()

    sample = MetricSample(
        metric="cpu_usage",
        value=42.5,
        unit="%",
        timestamp=TIMESTAMP,
    )

    instance.metrics = (
        sample,
    )

    snapshot = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    assert snapshot.metric is not None
    assert snapshot.metric.samples == (
        sample,
    )


def test_multiple_metric_aggregates_are_merged() -> None:
    _, node, instance, service = make_context()

    cpu = MetricSample(
        metric="cpu_usage",
        value=42.5,
        unit="%",
        timestamp=TIMESTAMP,
    )

    bitrate = MetricSample(
        metric="bitrate_out",
        value=18.65,
        unit="Mbps",
        timestamp=TIMESTAMP,
    )

    instance.metrics = (
        NodeMetric(samples=(cpu,)),
        NodeMetric(samples=(bitrate,)),
    )

    snapshot = service.build(
        node.node_id,
        instance.instance_id,
        timestamp=TIMESTAMP,
    )

    assert snapshot.metric is not None

    assert snapshot.metric.samples == (
        cpu,
        bitrate,
    )
