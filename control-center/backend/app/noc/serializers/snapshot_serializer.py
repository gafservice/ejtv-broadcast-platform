"""Canonical serialization and deserialization of NodeSnapshot.

ENG-013B — Node SDK
NCS references:
- 20-NODE-SNAPSHOT.md
- 23-SERIALIZATION.md
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Mapping

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
from app.noc.serializers.json_serializer import JsonSerializer


class SnapshotSerializer:
    """Serialize and deserialize canonical NodeSnapshot payloads."""

    def __init__(
        self,
        json_serializer: JsonSerializer | None = None,
    ) -> None:
        self._json = json_serializer or JsonSerializer()

    def to_dict(
        self,
        snapshot: NodeSnapshot,
    ) -> dict[str, Any]:
        if not isinstance(snapshot, NodeSnapshot):
            raise TypeError(
                "snapshot must be a NodeSnapshot"
            )

        payload: dict[str, Any] = {
            "node_id": self._node_id(snapshot),
            "node_type": snapshot.node_type.value,
            "instance_id": str(snapshot.instance_id),
            "snapshot_timestamp": (
                self._json.to_primitive(
                    snapshot.snapshot_timestamp
                )
            ),
        }

        if snapshot.info is not None:
            payload["info"] = {
                "instance_id": str(
                    snapshot.info.instance_id
                ),
                "hostname": snapshot.info.hostname,
                "platform": snapshot.info.platform,
                "operating_system": (
                    snapshot.info.operating_system
                ),
                "architecture": (
                    snapshot.info.architecture
                ),
                "runtime": snapshot.info.runtime,
                "boot_time": self._json.to_primitive(
                    snapshot.info.boot_time
                ),
            }

            if snapshot.info.fqdn is not None:
                payload["info"]["fqdn"] = (
                    snapshot.info.fqdn
                )

            if snapshot.info.location is not None:
                payload["info"]["location"] = (
                    snapshot.info.location
                )

            if snapshot.info.metadata is not None:
                payload["info"]["metadata"] = (
                    self._json.to_primitive(
                        snapshot.info.metadata
                    )
                )

        if snapshot.status is not None:
            payload["status"] = {
                "state": snapshot.status.state.value,
            }

        if snapshot.health is not None:
            payload["health"] = {
                "state": snapshot.health.state.value,
            }

        if snapshot.availability is not None:
            payload["availability"] = {
                "state": (
                    snapshot.availability.state.value
                ),
            }

        if snapshot.capability is not None:
            payload["capability"] = {
                "capabilities": [
                    {
                        key: value
                        for key, value in {
                            "name": capability.name,
                            "category": capability.category.value,
                            "enabled": capability.enabled,
                            "version": capability.version,
                        }.items()
                        if value is not None
                    }
                    for capability
                    in snapshot.capability.capabilities
                ]
            }

        if snapshot.capacity is not None:
            payload["capacity"] = {
                "resources": [
                    {
                        "resource": resource.resource,
                        "maximum": resource.maximum,
                        "allocated": resource.allocated,
                        "reserved": resource.reserved,
                        "available": resource.available,
                        "unit": resource.unit,
                    }
                    for resource
                    in snapshot.capacity.resources
                ]
            }

        if snapshot.metric is not None:
            payload["metric"] = {
                "samples": [
                    {
                        "metric": sample.metric,
                        "value": sample.value,
                        "unit": sample.unit,
                        "timestamp": (
                            self._json.to_primitive(
                                sample.timestamp
                            )
                        ),
                        "quality": sample.quality.value,
                    }
                    for sample
                    in snapshot.metric.samples
                ]
            }

        if snapshot.alarms is not None:
            payload["alarms"] = {
                "alarms": [
                    self._alarm(alarm)
                    for alarm
                    in snapshot.alarms.alarms
                ]
            }

        if snapshot.heartbeat is not None:
            payload["heartbeat"] = {
                "latest": (
                    self._heartbeat(
                        snapshot.heartbeat.latest
                    )
                    if snapshot.heartbeat.latest
                    is not None
                    else None
                )
            }

        return payload

    def dumps(
        self,
        snapshot: NodeSnapshot,
        *,
        indent: int | None = None,
    ) -> str:
        payload = self.to_dict(snapshot)

        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(
                (",", ":")
                if indent is None
                else (",", ": ")
            ),
            indent=indent,
        )

    def from_dict(
        self,
        payload: Mapping[str, Any],
    ) -> NodeSnapshot:
        """Build NodeSnapshot from canonical JSON-ready mapping."""
        if not isinstance(payload, Mapping):
            raise TypeError(
                "payload must be a mapping"
            )

        self._require_fields(
            payload,
            (
                "node_id",
                "node_type",
                "instance_id",
                "snapshot_timestamp",
            ),
        )

        node_id = self._parse_node_id(
            self._require_mapping(
                payload["node_id"],
                "node_id",
            )
        )

        instance_id = NodeInstanceId(
            self._require_string(
                payload["instance_id"],
                "instance_id",
            )
        )

        snapshot = NodeSnapshot(
            node_id=node_id,
            node_type=NodeType.from_value(
                self._require_string(
                    payload["node_type"],
                    "node_type",
                )
            ),
            instance_id=instance_id,
            snapshot_timestamp=self._parse_datetime(
                payload["snapshot_timestamp"],
                "snapshot_timestamp",
            ),
            info=self._parse_info(
                payload.get("info"),
                instance_id,
            ),
            status=self._parse_status(
                payload.get("status")
            ),
            health=self._parse_health(
                payload.get("health")
            ),
            availability=self._parse_availability(
                payload.get("availability")
            ),
            capability=self._parse_capability(
                payload.get("capability")
            ),
            capacity=self._parse_capacity(
                payload.get("capacity")
            ),
            metric=self._parse_metric(
                payload.get("metric")
            ),
            alarms=self._parse_alarms(
                payload.get("alarms")
            ),
            heartbeat=self._parse_heartbeat(
                payload.get("heartbeat")
            ),
        )

        return snapshot

    def loads(
        self,
        payload: str,
    ) -> NodeSnapshot:
        """Deserialize canonical JSON text into NodeSnapshot."""
        if not isinstance(payload, str):
            raise TypeError(
                "payload must be a JSON string"
            )

        decoded = json.loads(payload)

        if not isinstance(decoded, dict):
            raise ValueError(
                "NodeSnapshot JSON root must be an object"
            )

        return self.from_dict(decoded)

    def _node_id(
        self,
        snapshot: NodeSnapshot,
    ) -> dict[str, Any]:
        return {
            "id": snapshot.node_id.id,
            "name": snapshot.node_id.name,
            "display_name": (
                snapshot.node_id.display_name
            ),
            "created_at": self._json.to_primitive(
                snapshot.node_id.created_at
            ),
        }

    def _alarm(
        self,
        alarm: AlarmRecord,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "alarm_id": alarm.alarm_id,
            "alarm_type": alarm.alarm_type,
            "severity": alarm.severity.value,
            "state": alarm.state.value,
            "timestamp": self._json.to_primitive(
                alarm.timestamp
            ),
            "source": str(alarm.source),
            "title": alarm.title,
            "description": alarm.description,
            "acknowledged": alarm.acknowledged,
        }

        optional = {
            "acknowledged_by": (
                alarm.acknowledged_by
            ),
            "acknowledged_at": (
                self._json.to_primitive(
                    alarm.acknowledged_at
                )
                if alarm.acknowledged_at
                is not None
                else None
            ),
            "resolved_at": (
                self._json.to_primitive(
                    alarm.resolved_at
                )
                if alarm.resolved_at
                is not None
                else None
            ),
            "closed_at": (
                self._json.to_primitive(
                    alarm.closed_at
                )
                if alarm.closed_at
                is not None
                else None
            ),
            "correlation_id": (
                alarm.correlation_id
            ),
            "attributes": (
                self._json.to_primitive(
                    alarm.attributes
                )
                if alarm.attributes
                is not None
                else None
            ),
        }

        payload.update(
            {
                key: value
                for key, value in optional.items()
                if value is not None
            }
        )

        return payload

    def _heartbeat(
        self,
        heartbeat: HeartbeatRecord,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "heartbeat_id": heartbeat.heartbeat_id,
            "instance_id": str(
                heartbeat.instance_id
            ),
            "sequence": heartbeat.sequence,
            "timestamp": (
                self._json.to_primitive(
                    heartbeat.timestamp
                )
            ),
            "contract_version": (
                heartbeat.contract_version
            ),
            "uptime": heartbeat.uptime,
        }

        if heartbeat.checksum is not None:
            payload["checksum"] = heartbeat.checksum

        return payload

    def _parse_node_id(
        self,
        payload: Mapping[str, Any],
    ) -> NodeId:
        self._require_fields(
            payload,
            (
                "id",
                "name",
                "display_name",
                "created_at",
            ),
        )

        return NodeId(
            id=self._require_string(
                payload["id"],
                "node_id.id",
            ),
            name=self._require_string(
                payload["name"],
                "node_id.name",
            ),
            display_name=self._require_string(
                payload["display_name"],
                "node_id.display_name",
            ),
            created_at=self._parse_datetime(
                payload["created_at"],
                "node_id.created_at",
            ),
        )

    def _parse_info(
        self,
        value: Any,
        instance_id: NodeInstanceId,
    ) -> NodeInfo | None:
        if value is None:
            return None

        payload = self._require_mapping(
            value,
            "info",
        )

        self._require_fields(
            payload,
            (
                "instance_id",
                "hostname",
                "platform",
                "operating_system",
                "architecture",
                "runtime",
                "boot_time",
            ),
        )

        parsed_instance_id = NodeInstanceId(
            self._require_string(
                payload["instance_id"],
                "info.instance_id",
            )
        )

        if parsed_instance_id != instance_id:
            raise ValueError(
                "info.instance_id does not match snapshot instance_id"
            )

        metadata = payload.get("metadata")

        if metadata is not None:
            metadata = dict(
                self._require_mapping(
                    metadata,
                    "info.metadata",
                )
            )

        return NodeInfo(
            instance_id=parsed_instance_id,
            hostname=self._require_string(
                payload["hostname"],
                "info.hostname",
            ),
            platform=self._require_string(
                payload["platform"],
                "info.platform",
            ),
            operating_system=self._require_string(
                payload["operating_system"],
                "info.operating_system",
            ),
            architecture=self._require_string(
                payload["architecture"],
                "info.architecture",
            ),
            runtime=self._require_string(
                payload["runtime"],
                "info.runtime",
            ),
            boot_time=self._parse_datetime(
                payload["boot_time"],
                "info.boot_time",
            ),
            fqdn=self._optional_string(
                payload.get("fqdn"),
                "info.fqdn",
            ),
            location=self._optional_string(
                payload.get("location"),
                "info.location",
            ),
            metadata=metadata,
        )

    def _parse_status(
        self,
        value: Any,
    ) -> NodeStatus | None:
        if value is None:
            return None

        payload = self._require_mapping(
            value,
            "status",
        )

        return NodeStatus(
            NodeStatusState.from_value(
                self._require_string(
                    payload.get("state"),
                    "status.state",
                )
            )
        )

    def _parse_health(
        self,
        value: Any,
    ) -> NodeHealth | None:
        if value is None:
            return None

        payload = self._require_mapping(
            value,
            "health",
        )

        return NodeHealth(
            NodeHealthState.from_value(
                self._require_string(
                    payload.get("state"),
                    "health.state",
                )
            )
        )

    def _parse_availability(
        self,
        value: Any,
    ) -> NodeAvailability | None:
        if value is None:
            return None

        payload = self._require_mapping(
            value,
            "availability",
        )

        return NodeAvailability(
            NodeAvailabilityState.from_value(
                self._require_string(
                    payload.get("state"),
                    "availability.state",
                )
            )
        )

    def _parse_capability(
        self,
        value: Any,
    ) -> NodeCapability | None:
        if value is None:
            return None

        payload = self._require_mapping(
            value,
            "capability",
        )

        raw_capabilities = payload.get(
            "capabilities",
            [],
        )

        if not isinstance(raw_capabilities, list):
            raise TypeError(
                "capability.capabilities must be a list"
            )

        capabilities = []

        for index, raw in enumerate(
            raw_capabilities
        ):
            item = self._require_mapping(
                raw,
                f"capability.capabilities[{index}]",
            )

            capabilities.append(
                CapabilityDefinition(
                    name=self._require_string(
                        item.get("name"),
                        f"capability.capabilities[{index}].name",
                    ),
                    category=CapabilityCategory.from_value(
                        self._require_string(
                            item.get("category"),
                            f"capability.capabilities[{index}].category",
                        )
                    ),
                    enabled=self._require_bool(
                        item.get(
                            "enabled",
                            True,
                        ),
                        f"capability.capabilities[{index}].enabled",
                    ),
                    version=self._optional_string(
                        item.get("version"),
                        f"capability.capabilities[{index}].version",
                    ),
                )
            )

        return NodeCapability(
            capabilities=tuple(capabilities)
        )

    def _parse_capacity(
        self,
        value: Any,
    ) -> NodeCapacity | None:
        if value is None:
            return None

        payload = self._require_mapping(
            value,
            "capacity",
        )

        raw_resources = payload.get(
            "resources",
            [],
        )

        if not isinstance(raw_resources, list):
            raise TypeError(
                "capacity.resources must be a list"
            )

        resources = []

        for index, raw in enumerate(
            raw_resources
        ):
            item = self._require_mapping(
                raw,
                f"capacity.resources[{index}]",
            )

            resources.append(
                CapacityResource(
                    resource=self._require_string(
                        item.get("resource"),
                        f"capacity.resources[{index}].resource",
                    ),
                    maximum=self._require_number(
                        item.get("maximum"),
                        f"capacity.resources[{index}].maximum",
                    ),
                    allocated=self._require_number(
                        item.get("allocated"),
                        f"capacity.resources[{index}].allocated",
                    ),
                    reserved=self._require_number(
                        item.get("reserved"),
                        f"capacity.resources[{index}].reserved",
                    ),
                    available=self._require_number(
                        item.get("available"),
                        f"capacity.resources[{index}].available",
                    ),
                    unit=self._require_string(
                        item.get("unit"),
                        f"capacity.resources[{index}].unit",
                    ),
                )
            )

        return NodeCapacity(
            resources=tuple(resources)
        )

    def _parse_metric(
        self,
        value: Any,
    ) -> NodeMetric | None:
        if value is None:
            return None

        payload = self._require_mapping(
            value,
            "metric",
        )

        raw_samples = payload.get(
            "samples",
            [],
        )

        if not isinstance(raw_samples, list):
            raise TypeError(
                "metric.samples must be a list"
            )

        samples = []

        for index, raw in enumerate(
            raw_samples
        ):
            item = self._require_mapping(
                raw,
                f"metric.samples[{index}]",
            )

            samples.append(
                MetricSample(
                    metric=self._require_string(
                        item.get("metric"),
                        f"metric.samples[{index}].metric",
                    ),
                    value=self._require_number(
                        item.get("value"),
                        f"metric.samples[{index}].value",
                    ),
                    unit=self._require_string(
                        item.get("unit"),
                        f"metric.samples[{index}].unit",
                    ),
                    timestamp=self._parse_datetime(
                        item.get("timestamp"),
                        f"metric.samples[{index}].timestamp",
                    ),
                    quality=MetricQuality.from_value(
                        self._require_string(
                            item.get("quality"),
                            f"metric.samples[{index}].quality",
                        )
                    ),
                )
            )

        return NodeMetric(
            samples=tuple(samples)
        )

    def _parse_alarms(
        self,
        value: Any,
    ) -> NodeAlarm | None:
        if value is None:
            return None

        payload = self._require_mapping(
            value,
            "alarms",
        )

        raw_alarms = payload.get(
            "alarms",
            [],
        )

        if not isinstance(raw_alarms, list):
            raise TypeError(
                "alarms.alarms must be a list"
            )

        alarms = []

        for index, raw in enumerate(
            raw_alarms
        ):
            item = self._require_mapping(
                raw,
                f"alarms.alarms[{index}]",
            )

            attributes = item.get(
                "attributes"
            )

            if attributes is not None:
                attributes = dict(
                    self._require_mapping(
                        attributes,
                        f"alarms.alarms[{index}].attributes",
                    )
                )

            alarms.append(
                AlarmRecord(
                    alarm_id=self._require_string(
                        item.get("alarm_id"),
                        f"alarms.alarms[{index}].alarm_id",
                    ),
                    alarm_type=self._require_string(
                        item.get("alarm_type"),
                        f"alarms.alarms[{index}].alarm_type",
                    ),
                    severity=AlarmSeverity.from_value(
                        self._require_string(
                            item.get("severity"),
                            f"alarms.alarms[{index}].severity",
                        )
                    ),
                    state=AlarmState.from_value(
                        self._require_string(
                            item.get("state"),
                            f"alarms.alarms[{index}].state",
                        )
                    ),
                    timestamp=self._parse_datetime(
                        item.get("timestamp"),
                        f"alarms.alarms[{index}].timestamp",
                    ),
                    source=NodeInstanceId(
                        self._require_string(
                            item.get("source"),
                            f"alarms.alarms[{index}].source",
                        )
                    ),
                    title=self._require_string(
                        item.get("title"),
                        f"alarms.alarms[{index}].title",
                    ),
                    description=self._require_string(
                        item.get("description"),
                        f"alarms.alarms[{index}].description",
                    ),
                    acknowledged=self._require_bool(
                        item.get(
                            "acknowledged",
                            False,
                        ),
                        f"alarms.alarms[{index}].acknowledged",
                    ),
                    acknowledged_by=self._optional_string(
                        item.get(
                            "acknowledged_by"
                        ),
                        f"alarms.alarms[{index}].acknowledged_by",
                    ),
                    acknowledged_at=self._optional_datetime(
                        item.get(
                            "acknowledged_at"
                        ),
                        f"alarms.alarms[{index}].acknowledged_at",
                    ),
                    resolved_at=self._optional_datetime(
                        item.get(
                            "resolved_at"
                        ),
                        f"alarms.alarms[{index}].resolved_at",
                    ),
                    closed_at=self._optional_datetime(
                        item.get(
                            "closed_at"
                        ),
                        f"alarms.alarms[{index}].closed_at",
                    ),
                    correlation_id=self._optional_string(
                        item.get(
                            "correlation_id"
                        ),
                        f"alarms.alarms[{index}].correlation_id",
                    ),
                    attributes=attributes,
                )
            )

        return NodeAlarm(
            alarms=tuple(alarms)
        )

    def _parse_heartbeat(
        self,
        value: Any,
    ) -> NodeHeartbeat | None:
        if value is None:
            return None

        payload = self._require_mapping(
            value,
            "heartbeat",
        )

        latest = payload.get("latest")

        if latest is None:
            return NodeHeartbeat()

        item = self._require_mapping(
            latest,
            "heartbeat.latest",
        )

        return NodeHeartbeat(
            latest=HeartbeatRecord(
                heartbeat_id=self._require_string(
                    item.get("heartbeat_id"),
                    "heartbeat.latest.heartbeat_id",
                ),
                instance_id=NodeInstanceId(
                    self._require_string(
                        item.get("instance_id"),
                        "heartbeat.latest.instance_id",
                    )
                ),
                sequence=self._require_int(
                    item.get("sequence"),
                    "heartbeat.latest.sequence",
                ),
                timestamp=self._parse_datetime(
                    item.get("timestamp"),
                    "heartbeat.latest.timestamp",
                ),
                contract_version=self._require_string(
                    item.get("contract_version"),
                    "heartbeat.latest.contract_version",
                ),
                uptime=self._require_number(
                    item.get("uptime"),
                    "heartbeat.latest.uptime",
                ),
                checksum=self._optional_string(
                    item.get("checksum"),
                    "heartbeat.latest.checksum",
                ),
            )
        )

    @staticmethod
    def _parse_datetime(
        value: Any,
        field_name: str,
    ) -> datetime:
        text = SnapshotSerializer._require_string(
            value,
            field_name,
        )

        normalized = (
            text[:-1] + "+00:00"
            if text.endswith("Z")
            else text
        )

        try:
            parsed = datetime.fromisoformat(
                normalized
            )
        except ValueError as exc:
            raise ValueError(
                f"{field_name} must be valid ISO 8601 / RFC 3339"
            ) from exc

        if parsed.tzinfo is None:
            raise ValueError(
                f"{field_name} must include timezone information"
            )

        offset = parsed.utcoffset()

        if (
            offset is None
            or offset.total_seconds() != 0
        ):
            raise ValueError(
                f"{field_name} must be UTC"
            )

        return parsed

    @classmethod
    def _optional_datetime(
        cls,
        value: Any,
        field_name: str,
    ) -> datetime | None:
        if value is None:
            return None

        return cls._parse_datetime(
            value,
            field_name,
        )

    @staticmethod
    def _require_mapping(
        value: Any,
        field_name: str,
    ) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise TypeError(
                f"{field_name} must be an object"
            )

        return value

    @staticmethod
    def _require_fields(
        payload: Mapping[str, Any],
        fields: tuple[str, ...],
    ) -> None:
        missing = [
            field
            for field in fields
            if field not in payload
        ]

        if missing:
            raise ValueError(
                "Missing required field(s): "
                + ", ".join(missing)
            )

    @staticmethod
    def _require_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized

    @staticmethod
    def _optional_string(
        value: Any,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None

        return SnapshotSerializer._require_string(
            value,
            field_name,
        )

    @staticmethod
    def _require_bool(
        value: Any,
        field_name: str,
    ) -> bool:
        if not isinstance(value, bool):
            raise TypeError(
                f"{field_name} must be a bool"
            )

        return value

    @staticmethod
    def _require_number(
        value: Any,
        field_name: str,
    ) -> int | float:
        if isinstance(value, bool) or not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                f"{field_name} must be numeric"
            )

        return value

    @staticmethod
    def _require_int(
        value: Any,
        field_name: str,
    ) -> int:
        if isinstance(value, bool) or not isinstance(
            value,
            int,
        ):
            raise TypeError(
                f"{field_name} must be an integer"
            )

        return value
