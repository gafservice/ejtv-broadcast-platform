"""Tests for SnapshotSerializer.

ENG-013B — Node SDK
NCS references:
- 20-NODE-SNAPSHOT.md
- 23-SERIALIZATION.md
"""

import json
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
    MetricQuality,
    MetricSample,
    NodeMetric,
)
from app.noc.domain.node_snapshot import NodeSnapshot
from app.noc.domain.node_status import (
    NodeStatus,
    NodeStatusState,
)
from app.noc.domain.node_type import NodeType
from app.noc.serializers.snapshot_serializer import (
    SnapshotSerializer,
)


TIMESTAMP = datetime(
    2026,
    8,
    12,
    20,
    30,
    0,
    tzinfo=timezone.utc,
)


def make_node_id() -> NodeId:
    return NodeId(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
        created_at=TIMESTAMP,
    )


def make_minimal_snapshot() -> NodeSnapshot:
    return NodeSnapshot(
        node_id=make_node_id(),
        node_type=NodeType.STREAMING,
        instance_id=NodeInstanceId(
            "streaming-primary"
        ),
        snapshot_timestamp=TIMESTAMP,
    )


def make_complete_snapshot() -> NodeSnapshot:
    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    return NodeSnapshot(
        node_id=make_node_id(),
        node_type=NodeType.STREAMING,
        instance_id=instance_id,
        snapshot_timestamp=TIMESTAMP,

        info=NodeInfo(
            instance_id=instance_id,
            hostname="broadcast-node-01",
            fqdn="broadcast-node-01.local",
            platform="Bare Metal",
            operating_system="Ubuntu Server",
            architecture="x86_64",
            runtime="Python 3",
            location="San Jose",
            boot_time=TIMESTAMP - timedelta(
                hours=1
            ),
            metadata={
                "cluster": "primary",
            },
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
                    category=(
                        CapabilityCategory.PROTOCOL
                    ),
                    version="1.0",
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
                    timestamp=TIMESTAMP,
                    quality=MetricQuality.GOOD,
                ),
            )
        ),

        alarms=NodeAlarm(
            alarms=(
                AlarmRecord(
                    alarm_id="alm-001",
                    alarm_type="CPU_HIGH",
                    severity=AlarmSeverity.MAJOR,
                    state=AlarmState.ACTIVE,
                    timestamp=TIMESTAMP,
                    source=instance_id,
                    title="CPU high",
                    description=(
                        "CPU exceeded threshold."
                    ),
                    attributes={
                        "threshold": "95",
                    },
                ),
            )
        ),

        heartbeat=NodeHeartbeat(
            latest=HeartbeatRecord(
                heartbeat_id="hb-001",
                instance_id=instance_id,
                sequence=100,
                timestamp=TIMESTAMP,
                contract_version="1.0.0",
                uptime=3600,
            )
        ),
    )


def test_serializer_rejects_wrong_type() -> None:
    serializer = SnapshotSerializer()

    with pytest.raises(TypeError):
        serializer.to_dict(
            "snapshot"  # type: ignore[arg-type]
        )


def test_minimal_snapshot_contains_identity() -> None:
    payload = SnapshotSerializer().to_dict(
        make_minimal_snapshot()
    )

    assert payload["node_type"] == "STREAMING"
    assert (
        payload["instance_id"]
        == "streaming-primary"
    )

    assert (
        payload["snapshot_timestamp"]
        == "2026-08-12T20:30:00Z"
    )


def test_node_id_has_canonical_shape() -> None:
    payload = SnapshotSerializer().to_dict(
        make_minimal_snapshot()
    )

    assert payload["node_id"] == {
        "id": "streaming-core",
        "name": "streaming",
        "display_name": "Streaming Core",
        "created_at": (
            "2026-08-12T20:30:00Z"
        ),
    }


def test_optional_components_are_omitted() -> None:
    payload = SnapshotSerializer().to_dict(
        make_minimal_snapshot()
    )

    assert "info" not in payload
    assert "status" not in payload
    assert "health" not in payload
    assert "availability" not in payload
    assert "capability" not in payload
    assert "capacity" not in payload
    assert "metric" not in payload
    assert "alarms" not in payload
    assert "heartbeat" not in payload


def test_status_is_serialized() -> None:
    snapshot = make_minimal_snapshot()

    object.__setattr__(
        snapshot,
        "status",
        NodeStatus(NodeStatusState.RUNNING),
    )

    payload = SnapshotSerializer().to_dict(
        snapshot
    )

    assert payload["status"] == {
        "state": "RUNNING",
    }


def test_complete_snapshot_serializes_info() -> None:
    payload = SnapshotSerializer().to_dict(
        make_complete_snapshot()
    )

    assert payload["info"]["instance_id"] == (
        "streaming-primary"
    )

    assert payload["info"]["hostname"] == (
        "broadcast-node-01"
    )

    assert payload["info"]["metadata"] == {
        "cluster": "primary",
    }


def test_complete_snapshot_serializes_operational_state() -> None:
    payload = SnapshotSerializer().to_dict(
        make_complete_snapshot()
    )

    assert payload["status"] == {
        "state": "RUNNING",
    }

    assert payload["health"] == {
        "state": "HEALTHY",
    }

    assert payload["availability"] == {
        "state": "AVAILABLE",
    }


def test_capability_is_serialized() -> None:
    payload = SnapshotSerializer().to_dict(
        make_complete_snapshot()
    )

    assert payload["capability"] == {
        "capabilities": [
            {
                "name": "SRT",
                "category": "PROTOCOL",
                "enabled": True,
                "version": "1.0",
            }
        ]
    }


def test_capacity_is_serialized() -> None:
    payload = SnapshotSerializer().to_dict(
        make_complete_snapshot()
    )

    resource = (
        payload["capacity"]["resources"][0]
    )

    assert resource == {
        "resource": "Streaming Channels",
        "maximum": 16,
        "allocated": 10,
        "reserved": 2,
        "available": 4,
        "unit": "channels",
    }


def test_metric_is_serialized() -> None:
    payload = SnapshotSerializer().to_dict(
        make_complete_snapshot()
    )

    sample = payload["metric"]["samples"][0]

    assert sample == {
        "metric": "cpu_usage",
        "value": 42.5,
        "unit": "%",
        "timestamp": (
            "2026-08-12T20:30:00Z"
        ),
        "quality": "GOOD",
    }


def test_alarm_is_serialized() -> None:
    payload = SnapshotSerializer().to_dict(
        make_complete_snapshot()
    )

    alarm = payload["alarms"]["alarms"][0]

    assert alarm["alarm_id"] == "alm-001"
    assert alarm["alarm_type"] == "CPU_HIGH"
    assert alarm["severity"] == "MAJOR"
    assert alarm["state"] == "ACTIVE"
    assert alarm["source"] == (
        "streaming-primary"
    )

    assert alarm["attributes"] == {
        "threshold": "95",
    }


def test_heartbeat_is_serialized() -> None:
    payload = SnapshotSerializer().to_dict(
        make_complete_snapshot()
    )

    heartbeat = payload["heartbeat"]["latest"]

    assert heartbeat == {
        "heartbeat_id": "hb-001",
        "instance_id": "streaming-primary",
        "sequence": 100,
        "timestamp": (
            "2026-08-12T20:30:00Z"
        ),
        "contract_version": "1.0.0",
        "uptime": 3600,
    }


def test_dumps_produces_valid_json() -> None:
    serializer = SnapshotSerializer()

    encoded = serializer.dumps(
        make_complete_snapshot()
    )

    decoded = json.loads(encoded)

    assert decoded["node_type"] == (
        "STREAMING"
    )


def test_dumps_is_deterministic() -> None:
    serializer = SnapshotSerializer()
    snapshot = make_complete_snapshot()

    first = serializer.dumps(snapshot)
    second = serializer.dumps(snapshot)

    assert first == second


def test_pretty_json_is_supported() -> None:
    encoded = SnapshotSerializer().dumps(
        make_minimal_snapshot(),
        indent=2,
    )

    assert "\n" in encoded

    assert json.loads(encoded)[
        "instance_id"
    ] == "streaming-primary"


def test_serialization_does_not_modify_snapshot() -> None:
    snapshot = make_complete_snapshot()

    original_status = snapshot.status
    original_health = snapshot.health
    original_heartbeat = snapshot.heartbeat

    SnapshotSerializer().to_dict(snapshot)

    assert snapshot.status is original_status
    assert snapshot.health is original_health
    assert (
        snapshot.heartbeat
        is original_heartbeat
    )
