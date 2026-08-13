"""Tests for HeartbeatService.

ENG-013B — Node SDK
NCS reference: 19-NODE-HEARTBEAT.md
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_heartbeat import (
    HeartbeatRecord,
    NodeHeartbeat,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import (
    NodeNotFoundError,
    NodeRegistry,
)
from app.noc.services.heartbeat_service import (
    DuplicateHeartbeatError,
    HeartbeatDisposition,
    HeartbeatInstanceMismatchError,
    HeartbeatService,
    NodeInstanceNotFoundError,
    OutOfOrderHeartbeatError,
)


class MemoryRepository:
    def __init__(self) -> None:
        self.nodes = {}

    def save(self, node):
        self.nodes[node.node_id.id] = node

    def get(self, node_id):
        return self.nodes.get(
            node_id.id
        )

    def exists(self, node_id):
        return node_id.id in self.nodes

    def list_all(self):
        return tuple(
            self.nodes.values()
        )

    def delete(self, node_id):
        return (
            self.nodes.pop(
                node_id.id,
                None,
            )
            is not None
        )

    def count(self):
        return len(self.nodes)


BASE_TIME = datetime(
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

    return (
        repository,
        registry,
        node,
        instance,
        HeartbeatService(registry),
    )


def make_record(
    *,
    sequence: int = 1,
    timestamp: datetime = BASE_TIME,
    uptime: float = 100.0,
    heartbeat_id: str | None = None,
    instance_id: str = "streaming-primary",
) -> HeartbeatRecord:
    return HeartbeatRecord(
        heartbeat_id=(
            heartbeat_id
            or f"hb-{sequence}"
        ),
        instance_id=NodeInstanceId(
            instance_id
        ),
        sequence=sequence,
        timestamp=timestamp,
        contract_version="1.0.0",
        uptime=uptime,
    )


def test_service_requires_registry() -> None:
    with pytest.raises(TypeError):
        HeartbeatService(
            object()  # type: ignore[arg-type]
        )


def test_first_heartbeat_is_accepted() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    receipt = service.receive(
        node.node_id,
        instance.instance_id,
        make_record(sequence=1),
    )

    assert receipt.disposition is (
        HeartbeatDisposition.FIRST
    )

    assert receipt.previous is None
    assert receipt.record.sequence == 1
    assert receipt.missing_sequences == 0


def test_first_heartbeat_is_stored_on_instance() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    record = make_record(sequence=1)

    service.receive(
        node.node_id,
        instance.instance_id,
        record,
    )

    assert isinstance(
        instance.heartbeat,
        NodeHeartbeat,
    )

    assert instance.heartbeat.latest is (
        record
    )


def test_contiguous_heartbeat_replaces_previous() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    first = make_record(
        sequence=10,
        timestamp=BASE_TIME,
        uptime=100,
    )

    second = make_record(
        sequence=11,
        timestamp=BASE_TIME + timedelta(
            seconds=5
        ),
        uptime=105,
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

    assert receipt.disposition is (
        HeartbeatDisposition.CONTIGUOUS
    )

    assert receipt.previous is first
    assert receipt.record is second
    assert instance.heartbeat.latest is second


def test_gap_is_detected() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        make_record(sequence=10),
    )

    receipt = service.receive(
        node.node_id,
        instance.instance_id,
        make_record(
            sequence=14,
            timestamp=BASE_TIME
            + timedelta(seconds=5),
            uptime=105,
        ),
    )

    assert receipt.disposition is (
        HeartbeatDisposition.GAP
    )

    assert receipt.detected_gap is True
    assert receipt.missing_sequences == 3


def test_duplicate_id_is_rejected() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        make_record(
            sequence=10,
            heartbeat_id="hb-fixed",
        ),
    )

    with pytest.raises(
        DuplicateHeartbeatError
    ):
        service.receive(
            node.node_id,
            instance.instance_id,
            make_record(
                sequence=11,
                timestamp=BASE_TIME
                + timedelta(seconds=5),
                uptime=105,
                heartbeat_id="hb-fixed",
            ),
        )


def test_duplicate_sequence_is_rejected() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        make_record(
            sequence=10,
            heartbeat_id="hb-a",
        ),
    )

    with pytest.raises(
        DuplicateHeartbeatError
    ):
        service.receive(
            node.node_id,
            instance.instance_id,
            make_record(
                sequence=10,
                timestamp=BASE_TIME
                + timedelta(seconds=1),
                uptime=101,
                heartbeat_id="hb-b",
            ),
        )


def test_older_sequence_is_rejected() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        make_record(sequence=10),
    )

    with pytest.raises(
        OutOfOrderHeartbeatError
    ):
        service.receive(
            node.node_id,
            instance.instance_id,
            make_record(
                sequence=9,
                timestamp=BASE_TIME
                + timedelta(seconds=1),
                uptime=101,
            ),
        )


def test_older_timestamp_is_rejected() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        make_record(
            sequence=10,
            timestamp=BASE_TIME,
        ),
    )

    with pytest.raises(
        OutOfOrderHeartbeatError
    ):
        service.receive(
            node.node_id,
            instance.instance_id,
            make_record(
                sequence=11,
                timestamp=BASE_TIME
                - timedelta(seconds=1),
                uptime=101,
            ),
        )


def test_restart_allows_sequence_reset() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    first = make_record(
        sequence=500,
        timestamp=BASE_TIME,
        uptime=7200,
    )

    restarted = make_record(
        sequence=1,
        timestamp=BASE_TIME
        + timedelta(seconds=10),
        uptime=4,
        heartbeat_id="hb-after-restart",
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        first,
    )

    receipt = service.receive(
        node.node_id,
        instance.instance_id,
        restarted,
    )

    assert receipt.disposition is (
        HeartbeatDisposition.RESTART
    )

    assert receipt.detected_restart is True
    assert receipt.record.sequence == 1


def test_unknown_node_is_rejected() -> None:
    _, _, _, instance, service = (
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
        service.receive(
            unknown,
            instance.instance_id,
            make_record(),
        )


def test_unknown_instance_is_rejected() -> None:
    _, _, node, _, service = (
        make_context()
    )

    unknown = NodeInstanceId(
        "streaming-backup"
    )

    with pytest.raises(
        NodeInstanceNotFoundError
    ):
        service.receive(
            node.node_id,
            unknown,
            make_record(
                instance_id="streaming-backup"
            ),
        )


def test_record_instance_mismatch_is_rejected() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    with pytest.raises(
        HeartbeatInstanceMismatchError
    ):
        service.receive(
            node.node_id,
            instance.instance_id,
            make_record(
                instance_id="streaming-backup"
            ),
        )


def test_latest_returns_empty_before_first_heartbeat() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    heartbeat = service.latest(
        node.node_id,
        instance.instance_id,
    )

    assert heartbeat.is_present is False
    assert heartbeat.latest is None


def test_latest_returns_last_accepted_heartbeat() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    record = make_record(sequence=42)

    service.receive(
        node.node_id,
        instance.instance_id,
        record,
    )

    heartbeat = service.latest(
        node.node_id,
        instance.instance_id,
    )

    assert heartbeat.latest is record


def test_is_present_false_before_first_heartbeat() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    assert service.is_present(
        node.node_id,
        instance.instance_id,
    ) is False


def test_is_present_true_after_heartbeat() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        make_record(),
    )

    assert service.is_present(
        node.node_id,
        instance.instance_id,
    ) is True


def test_rejected_heartbeat_does_not_replace_latest() -> None:
    _, _, node, instance, service = (
        make_context()
    )

    accepted = make_record(
        sequence=10,
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        accepted,
    )

    with pytest.raises(
        OutOfOrderHeartbeatError
    ):
        service.receive(
            node.node_id,
            instance.instance_id,
            make_record(
                sequence=9,
                timestamp=BASE_TIME
                + timedelta(seconds=1),
                uptime=101,
            ),
        )

    assert service.latest(
        node.node_id,
        instance.instance_id,
    ).latest is accepted


def test_service_does_not_modify_node_status_or_health() -> None:
    """Heartbeat presence must remain independent of state/health."""
    _, _, node, instance, service = (
        make_context()
    )

    original_status = getattr(
        instance,
        "status",
        None,
    )

    original_health = getattr(
        instance,
        "health",
        None,
    )

    service.receive(
        node.node_id,
        instance.instance_id,
        make_record(),
    )

    assert getattr(
        instance,
        "status",
        None,
    ) is original_status

    assert getattr(
        instance,
        "health",
        None,
    ) is original_health
