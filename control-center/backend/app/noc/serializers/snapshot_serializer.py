"""Canonical JSON representation of NodeSnapshot.

ENG-013B — Node SDK
NCS references:
- 20-NODE-SNAPSHOT.md
- 23-SERIALIZATION.md
"""

from __future__ import annotations

import json
from typing import Any

from app.noc.domain.node_snapshot import NodeSnapshot
from app.noc.serializers.json_serializer import JsonSerializer


class SnapshotSerializer:
    """Serialize NodeSnapshot into its canonical wire representation.

    This serializer does not validate or modify the domain model.
    Contract validation must occur before serialization.
    """

    def __init__(
        self,
        json_serializer: JsonSerializer | None = None,
    ) -> None:
        self._json = json_serializer or JsonSerializer()

    def to_dict(
        self,
        snapshot: NodeSnapshot,
    ) -> dict[str, Any]:
        """Convert NodeSnapshot to its canonical JSON-ready mapping."""
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
                            "category": (
                                capability.category.value
                            ),
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
                        "quality": (
                            sample.quality.value
                        ),
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
        """Serialize NodeSnapshot to deterministic JSON text."""
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
        alarm: Any,
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
        heartbeat: Any,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "heartbeat_id": (
                heartbeat.heartbeat_id
            ),
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
            payload["checksum"] = (
                heartbeat.checksum
            )

        return payload
