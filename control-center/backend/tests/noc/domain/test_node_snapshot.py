"""Tests for NodeSnapshot.

ENG-013B — Node SDK
NCS reference: 20-NODE-SNAPSHOT.md
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
    NodeAlarm,
)
from app.noc.domain.node_availability import (
    NodeAvailability,
    NodeAvailabilityState,
)
from app.noc.domain.node_capacity import (
    CapacityResource,
    NodeCapacity,
)
from app.noc.domain.node_capability import (
    CapabilityCategory,
    CapabilityDefinition,
    NodeCapability,
)
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_heartbeat import (
    HeartbeatRecord,
    NodeHeartbeat,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_info import NodeInfo
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


def now() -> datetime:
    return datetime.now(timezone.utc)


def make_node_id() -> NodeId:
    return NodeId.create(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
    )


def make_instance_id() -> NodeInstanceId:
    return NodeInstanceId("streaming-primary")


def make_complete_snapshot() -> NodeSnapshot:
    instance_id = make_instance_id()
    timestamp = now()

    return NodeSnapshot(
        node_id=make_node_id(),
        node_type=NodeType.STREAMING,
        instance_id=instance_id,
        snapshot_timestamp=timestamp,
        info=NodeInfo(
            instance_id=instance_id,
            hostname="broadcast-node-01",
            platform="Bare Metal",
            operating_system="Ubuntu Server 24.04 LTS",
            architecture="x86_64",
            runtime="Python 3",
            boot_time=timestamp - timedelta(hours=1),
        ),
        status=NodeStatus(
            NodeStatusState.RUNNING
        ),
        health=NodeHealth(
            NodeHealthState.HEALTHY
        ),
        availability=NodeAvailability(
            NodeAvailabilityState.AVAILABLE
        ),
        capability=NodeCapability(
            capabilities=(
                CapabilityDefinition(
                    name="SRT",
                    category=CapabilityCategory.PROTOCOL,
                ),
            )
        ),
        capacity=NodeCapacity(
            resources=(
                CapacityResource(
                    resource="Streaming Channels",
                    maximum=16,
                    allocated=10,
                    reserved=2,
                    available=4,
                    unit="channels",
                ),
            )
        ),
        metric=NodeMetric(
            samples=(
                MetricSample(
                    metric="cpu_usage",
                    value=42.5,
                    unit="%",
                    timestamp=timestamp,
                ),
            )
        ),
        alarms=NodeAlarm(),
        heartbeat=NodeHeartbeat(
            latest=HeartbeatRecord(
                heartbeat_id="hb-001",
                instance_id=instance_id,
                sequence=100,
                timestamp=timestamp,
                contract_version="1.0.0",
                uptime=3600,
            )
        ),
    )


def test_snapshot_can_be_minimal() -> None:
    snapshot = NodeSnapshot(
        node_id=make_node_id(),
        node_type=NodeType.STREAMING,
        instance_id=make_instance_id(),
        snapshot_timestamp=now(),
    )

    assert snapshot.info is None
    assert snapshot.status is None
    assert snapshot.health is None
    assert snapshot.is_complete is False


def test_snapshot_can_be_complete() -> None:
    snapshot = make_complete_snapshot()

    assert snapshot.is_complete is True
    assert snapshot.has_info is True
    assert snapshot.has_status is True
    assert snapshot.has_health is True
    assert snapshot.has_availability is True
    assert snapshot.has_capability is True
    assert snapshot.has_capacity is True
    assert snapshot.has_metrics is True
    assert snapshot.has_heartbeat is True


def test_snapshot_rejects_invalid_node_id() -> None:
    with pytest.raises(TypeError):
        NodeSnapshot(
            node_id="streaming-core",  # type: ignore[arg-type]
            node_type=NodeType.STREAMING,
            instance_id=make_instance_id(),
            snapshot_timestamp=now(),
        )


def test_snapshot_rejects_invalid_node_type() -> None:
    with pytest.raises(TypeError):
        NodeSnapshot(
            node_id=make_node_id(),
            node_type="STREAMING",  # type: ignore[arg-type]
            instance_id=make_instance_id(),
            snapshot_timestamp=now(),
        )


def test_snapshot_rejects_invalid_instance_id() -> None:
    with pytest.raises(TypeError):
        NodeSnapshot(
            node_id=make_node_id(),
            node_type=NodeType.STREAMING,
            instance_id="streaming-primary",  # type: ignore[arg-type]
            snapshot_timestamp=now(),
        )


def test_snapshot_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError):
        NodeSnapshot(
            node_id=make_node_id(),
            node_type=NodeType.STREAMING,
            instance_id=make_instance_id(),
            snapshot_timestamp=datetime(
                2026,
                8,
                11,
                19,
                0,
            ),
        )


def test_snapshot_rejects_non_utc_timestamp() -> None:
    non_utc = timezone(
        timedelta(hours=-6)
    )

    with pytest.raises(ValueError):
        NodeSnapshot(
            node_id=make_node_id(),
            node_type=NodeType.STREAMING,
            instance_id=make_instance_id(),
            snapshot_timestamp=datetime(
                2026,
                8,
                11,
                13,
                0,
                tzinfo=non_utc,
            ),
        )


def test_snapshot_rejects_info_from_other_instance() -> None:
    with pytest.raises(ValueError):
        NodeSnapshot(
            node_id=make_node_id(),
            node_type=NodeType.STREAMING,
            instance_id=make_instance_id(),
            snapshot_timestamp=now(),
            info=NodeInfo(
                instance_id=NodeInstanceId(
                    "streaming-backup"
                ),
                hostname="backup-node",
                platform="Bare Metal",
                operating_system="Ubuntu Server",
                architecture="x86_64",
                runtime="Python 3",
                boot_time=now(),
            ),
        )


def test_snapshot_accepts_active_alarm() -> None:
    instance_id = make_instance_id()
    timestamp = now()

    snapshot = NodeSnapshot(
        node_id=make_node_id(),
        node_type=NodeType.STREAMING,
        instance_id=instance_id,
        snapshot_timestamp=timestamp,
        alarms=NodeAlarm(
            alarms=(
                AlarmRecord(
                    alarm_id="alm-001",
                    alarm_type="CPU_HIGH",
                    severity=AlarmSeverity.MAJOR,
                    state=AlarmState.ACTIVE,
                    timestamp=timestamp,
                    source=instance_id,
                    title="CPU high",
                    description="CPU exceeded threshold.",
                ),
            )
        ),
    )

    assert snapshot.has_alarms is True
    assert snapshot.active_alarm_count == 1


def test_snapshot_rejects_resolved_alarm() -> None:
    instance_id = make_instance_id()
    timestamp = now()

    resolved = AlarmRecord(
        alarm_id="alm-001",
        alarm_type="CPU_HIGH",
        severity=AlarmSeverity.MAJOR,
        state=AlarmState.RESOLVED,
        timestamp=timestamp,
        source=instance_id,
        title="CPU high",
        description="CPU exceeded threshold.",
        resolved_at=timestamp + timedelta(minutes=1),
    )

    with pytest.raises(ValueError):
        NodeSnapshot(
            node_id=make_node_id(),
            node_type=NodeType.STREAMING,
            instance_id=instance_id,
            snapshot_timestamp=timestamp,
            alarms=NodeAlarm(
                alarms=(resolved,)
            ),
        )


def test_snapshot_rejects_alarm_from_other_instance() -> None:
    timestamp = now()

    alarm = AlarmRecord(
        alarm_id="alm-001",
        alarm_type="CPU_HIGH",
        severity=AlarmSeverity.MAJOR,
        state=AlarmState.ACTIVE,
        timestamp=timestamp,
        source=NodeInstanceId("streaming-backup"),
        title="CPU high",
        description="CPU exceeded threshold.",
    )

    with pytest.raises(ValueError):
        NodeSnapshot(
            node_id=make_node_id(),
            node_type=NodeType.STREAMING,
            instance_id=make_instance_id(),
            snapshot_timestamp=timestamp,
            alarms=NodeAlarm(
                alarms=(alarm,)
            ),
        )


def test_snapshot_accepts_heartbeat_from_same_instance() -> None:
    instance_id = make_instance_id()

    snapshot = NodeSnapshot(
        node_id=make_node_id(),
        node_type=NodeType.STREAMING,
        instance_id=instance_id,
        snapshot_timestamp=now(),
        heartbeat=NodeHeartbeat(
            latest=HeartbeatRecord(
                heartbeat_id="hb-001",
                instance_id=instance_id,
                sequence=1,
                timestamp=now(),
                contract_version="1.0.0",
                uptime=100,
            )
        ),
    )

    assert snapshot.has_heartbeat is True


def test_snapshot_rejects_heartbeat_from_other_instance() -> None:
    with pytest.raises(ValueError):
        NodeSnapshot(
            node_id=make_node_id(),
            node_type=NodeType.STREAMING,
            instance_id=make_instance_id(),
            snapshot_timestamp=now(),
            heartbeat=NodeHeartbeat(
                latest=HeartbeatRecord(
                    heartbeat_id="hb-001",
                    instance_id=NodeInstanceId(
                        "streaming-backup"
                    ),
                    sequence=1,
                    timestamp=now(),
                    contract_version="1.0.0",
                    uptime=100,
                )
            ),
        )


def test_snapshot_empty_alarm_collection_has_no_alarms() -> None:
    snapshot = NodeSnapshot(
        node_id=make_node_id(),
        node_type=NodeType.STREAMING,
        instance_id=make_instance_id(),
        snapshot_timestamp=now(),
        alarms=NodeAlarm(),
    )

    assert snapshot.has_alarms is False
    assert snapshot.active_alarm_count == 0


def test_snapshot_without_heartbeat_is_not_present() -> None:
    snapshot = NodeSnapshot(
        node_id=make_node_id(),
        node_type=NodeType.STREAMING,
        instance_id=make_instance_id(),
        snapshot_timestamp=now(),
    )

    assert snapshot.has_heartbeat is False


def test_snapshot_is_immutable() -> None:
    snapshot = make_complete_snapshot()

    with pytest.raises(AttributeError):
        snapshot.status = None  # type: ignore[misc]


def test_snapshot_string_representation() -> None:
    timestamp = datetime(
        2026,
        8,
        11,
        20,
        0,
        tzinfo=timezone.utc,
    )

    snapshot = NodeSnapshot(
        node_id=make_node_id(),
        node_type=NodeType.STREAMING,
        instance_id=make_instance_id(),
        snapshot_timestamp=timestamp,
    )

    assert str(snapshot) == (
        "streaming-core/streaming-primary "
        "@ 2026-08-11T20:00:00+00:00"
    )
