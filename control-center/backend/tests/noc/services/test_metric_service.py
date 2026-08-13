from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_metric import (
    MetricQuality,
    MetricSample,
)
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import (
    NodeNotFoundError,
    NodeRegistry,
)
from app.noc.services.metric_service import (
    DuplicateMetricError,
    MetricDisposition,
    MetricService,
    NodeInstanceNotFoundError,
    StaleMetricError,
)
from app.noc.services.snapshot_service import SnapshotService


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
        return self.nodes.pop(node_id.id, None) is not None

    def count(self):
        return len(self.nodes)


BASE_TIME = datetime(
    2026,
    8,
    13,
    21,
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

    return (
        repository,
        registry,
        node,
        instance,
        MetricService(registry),
    )


def make_sample(
    metric="cpu_usage",
    value=42.5,
    unit="%",
    timestamp=BASE_TIME,
    quality=MetricQuality.GOOD,
):
    return MetricSample(
        metric=metric,
        value=value,
        unit=unit,
        timestamp=timestamp,
        quality=quality,
    )


def test_service_requires_registry():
    with pytest.raises(TypeError):
        MetricService(
            object()  # type: ignore[arg-type]
        )


def test_first_metric_is_accepted():
    _, _, node, instance, service = make_context()

    sample = make_sample()

    receipt = service.receive(
        node.node_id,
        instance.instance_id,
        sample,
    )

    assert receipt.disposition is MetricDisposition.FIRST
    assert receipt.previous is None
    assert receipt.sample is sample


def test_second_different_metric_is_added():
    _, _, node, instance, service = make_context()

    service.receive(
        node.node_id,
        instance.instance_id,
        make_sample(),
    )

    bitrate = make_sample(
        metric="bitrate_out",
        value=18.65,
        unit="Mbps",
    )

    receipt = service.receive(
        node.node_id,
        instance.instance_id,
        bitrate,
    )

    assert receipt.disposition is MetricDisposition.ADDED
    assert len(receipt.metrics.samples) == 2


def test_newer_same_metric_replaces_previous():
    _, _, node, instance, service = make_context()

    first = make_sample(
        value=42.5,
    )

    second = make_sample(
        value=55.0,
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        first,
    )

    receipt = service.receive(
        node.node_id,
        instance.instance_id,
        second,
    )

    assert receipt.disposition is MetricDisposition.REPLACED
    assert receipt.previous is first
    assert receipt.replaced is True

    current = service.current(
        node.node_id,
        instance.instance_id,
    )

    assert current.get("cpu_usage") is second
    assert len(current.samples) == 1


def test_same_sample_is_duplicate():
    _, _, node, instance, service = make_context()

    sample = make_sample()

    service.receive(
        node.node_id,
        instance.instance_id,
        sample,
    )

    with pytest.raises(DuplicateMetricError):
        service.receive(
            node.node_id,
            instance.instance_id,
            sample,
        )


def test_same_timestamp_same_metric_is_duplicate():
    _, _, node, instance, service = make_context()

    service.receive(
        node.node_id,
        instance.instance_id,
        make_sample(value=42.5),
    )

    with pytest.raises(DuplicateMetricError):
        service.receive(
            node.node_id,
            instance.instance_id,
            make_sample(value=50.0),
        )


def test_older_metric_is_stale():
    _, _, node, instance, service = make_context()

    service.receive(
        node.node_id,
        instance.instance_id,
        make_sample(
            timestamp=BASE_TIME + timedelta(seconds=5)
        ),
    )

    with pytest.raises(StaleMetricError):
        service.receive(
            node.node_id,
            instance.instance_id,
            make_sample(
                timestamp=BASE_TIME
            ),
        )


def test_metric_names_are_case_insensitive():
    _, _, node, instance, service = make_context()

    first = make_sample(
        metric="CPU_USAGE",
        value=42.5,
    )

    second = make_sample(
        metric="cpu_usage",
        value=55.0,
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        first,
    )

    receipt = service.receive(
        node.node_id,
        instance.instance_id,
        second,
    )

    assert receipt.disposition is MetricDisposition.REPLACED
    assert len(receipt.metrics.samples) == 1


def test_invalid_quality_is_preserved():
    _, _, node, instance, service = make_context()

    sample = make_sample(
        quality=MetricQuality.INVALID
    )

    receipt = service.receive(
        node.node_id,
        instance.instance_id,
        sample,
    )

    assert receipt.sample.quality is MetricQuality.INVALID

    current = service.current(
        node.node_id,
        instance.instance_id,
    )

    assert current.get("cpu_usage").quality is MetricQuality.INVALID


def test_current_empty_returns_empty_node_metric():
    _, _, node, instance, service = make_context()

    current = service.current(
        node.node_id,
        instance.instance_id,
    )

    assert current.samples == ()


def test_unknown_node_is_rejected():
    _, _, _, instance, service = make_context()

    unknown = NodeId.create(
        id="unknown-node",
        name="unknown",
        display_name="Unknown",
    )

    with pytest.raises(NodeNotFoundError):
        service.receive(
            unknown,
            instance.instance_id,
            make_sample(),
        )


def test_unknown_instance_is_rejected():
    _, _, node, _, service = make_context()

    with pytest.raises(NodeInstanceNotFoundError):
        service.receive(
            node.node_id,
            NodeInstanceId("streaming-backup"),
            make_sample(),
        )


def test_rejected_stale_metric_does_not_replace_current():
    _, _, node, instance, service = make_context()

    accepted = make_sample(
        value=60.0,
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        accepted,
    )

    with pytest.raises(StaleMetricError):
        service.receive(
            node.node_id,
            instance.instance_id,
            make_sample(
                value=20.0,
                timestamp=BASE_TIME,
            ),
        )

    current = service.current(
        node.node_id,
        instance.instance_id,
    )

    assert current.get("cpu_usage") is accepted


def test_metrics_coexist():
    _, _, node, instance, service = make_context()

    cpu = make_sample(
        metric="cpu_usage",
        value=42.5,
        unit="%",
    )

    bitrate = make_sample(
        metric="bitrate_out",
        value=18.65,
        unit="Mbps",
    )

    loss = make_sample(
        metric="packet_loss",
        value=0.2,
        unit="%",
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        cpu,
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        bitrate,
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        loss,
    )

    current = service.current(
        node.node_id,
        instance.instance_id,
    )

    assert len(current.samples) == 3
    assert current.get("cpu_usage") is cpu
    assert current.get("bitrate_out") is bitrate
    assert current.get("packet_loss") is loss


def test_snapshot_contains_current_metrics():
    _, registry, node, instance, service = make_context()

    cpu = make_sample(
        metric="cpu_usage",
        value=42.5,
        unit="%",
    )

    bitrate = make_sample(
        metric="bitrate_out",
        value=18.65,
        unit="Mbps",
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        cpu,
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        bitrate,
    )

    snapshot = SnapshotService(
        registry
    ).build(
        node.node_id,
        instance.instance_id,
        timestamp=BASE_TIME,
    )

    assert snapshot.metric is not None
    assert snapshot.metric.get("cpu_usage") == cpu
    assert snapshot.metric.get("bitrate_out") == bitrate


def test_instance_metrics_store_current_samples():
    _, _, node, instance, service = make_context()

    sample = make_sample()

    service.receive(
        node.node_id,
        instance.instance_id,
        sample,
    )

    assert instance.metrics == (
        sample,
    )


def test_receive_rejects_wrong_sample_type():
    _, _, node, instance, service = make_context()

    with pytest.raises(TypeError):
        service.receive(
            node.node_id,
            instance.instance_id,
            "cpu=42"  # type: ignore[arg-type]
        )
