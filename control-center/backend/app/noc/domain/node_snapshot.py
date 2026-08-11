"""Consistent operational snapshot of a NodeInstance.

ENG-013B — Node SDK
NCS reference: 20-NODE-SNAPSHOT.md
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.noc.domain.node_alarm import NodeAlarm
from app.noc.domain.node_availability import NodeAvailability
from app.noc.domain.node_capacity import NodeCapacity
from app.noc.domain.node_capability import NodeCapability
from app.noc.domain.node_health import NodeHealth
from app.noc.domain.node_heartbeat import NodeHeartbeat
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_info import NodeInfo
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_metric import NodeMetric
from app.noc.domain.node_status import NodeStatus
from app.noc.domain.node_type import NodeType


@dataclass(frozen=True, slots=True)
class NodeSnapshot:
    """Immutable operational view of one NodeInstance.

    A NodeSnapshot groups the current operational dimensions defined
    by the Node Contract Specification without changing their meaning.

    Events are intentionally excluded because they represent history,
    while a Snapshot represents current state only.
    """

    node_id: NodeId
    node_type: NodeType
    instance_id: NodeInstanceId
    snapshot_timestamp: datetime

    info: NodeInfo | None = None
    status: NodeStatus | None = None
    health: NodeHealth | None = None
    availability: NodeAvailability | None = None

    capability: NodeCapability | None = None
    capacity: NodeCapacity | None = None

    metric: NodeMetric | None = None
    alarms: NodeAlarm | None = None
    heartbeat: NodeHeartbeat | None = None

    def __post_init__(self) -> None:
        """Validate snapshot identity and cross-component coherence."""
        if not isinstance(self.node_id, NodeId):
            raise TypeError(
                "NodeSnapshot.node_id must be a NodeId"
            )

        if not isinstance(self.node_type, NodeType):
            raise TypeError(
                "NodeSnapshot.node_type must be a NodeType"
            )

        if not isinstance(self.instance_id, NodeInstanceId):
            raise TypeError(
                "NodeSnapshot.instance_id must be a NodeInstanceId"
            )

        self._validate_utc_datetime(
            self.snapshot_timestamp,
            "snapshot_timestamp",
        )

        self._validate_optional_type(
            self.info,
            NodeInfo,
            "info",
        )

        self._validate_optional_type(
            self.status,
            NodeStatus,
            "status",
        )

        self._validate_optional_type(
            self.health,
            NodeHealth,
            "health",
        )

        self._validate_optional_type(
            self.availability,
            NodeAvailability,
            "availability",
        )

        self._validate_optional_type(
            self.capability,
            NodeCapability,
            "capability",
        )

        self._validate_optional_type(
            self.capacity,
            NodeCapacity,
            "capacity",
        )

        self._validate_optional_type(
            self.metric,
            NodeMetric,
            "metric",
        )

        self._validate_optional_type(
            self.alarms,
            NodeAlarm,
            "alarms",
        )

        self._validate_optional_type(
            self.heartbeat,
            NodeHeartbeat,
            "heartbeat",
        )

        self._validate_instance_coherence()
        self._validate_alarm_scope()
        self._validate_heartbeat_scope()

    @property
    def has_info(self) -> bool:
        return self.info is not None

    @property
    def has_status(self) -> bool:
        return self.status is not None

    @property
    def has_health(self) -> bool:
        return self.health is not None

    @property
    def has_availability(self) -> bool:
        return self.availability is not None

    @property
    def has_capability(self) -> bool:
        return self.capability is not None

    @property
    def has_capacity(self) -> bool:
        return self.capacity is not None

    @property
    def has_metrics(self) -> bool:
        return self.metric is not None

    @property
    def has_alarms(self) -> bool:
        return (
            self.alarms is not None
            and len(self.alarms) > 0
        )

    @property
    def has_heartbeat(self) -> bool:
        return (
            self.heartbeat is not None
            and self.heartbeat.is_present
        )

    @property
    def active_alarm_count(self) -> int:
        if self.alarms is None:
            return 0

        return len(self.alarms.active)

    @property
    def is_complete(self) -> bool:
        """Return whether all principal snapshot dimensions exist.

        This is an SDK convenience property, not a NCS conformance
        requirement. The NCS explicitly permits omitted components.
        """
        return all(
            (
                self.info is not None,
                self.status is not None,
                self.health is not None,
                self.availability is not None,
                self.capability is not None,
                self.capacity is not None,
                self.metric is not None,
                self.alarms is not None,
                self.heartbeat is not None,
            )
        )

    def _validate_instance_coherence(self) -> None:
        if (
            self.info is not None
            and self.info.instance_id != self.instance_id
        ):
            raise ValueError(
                "NodeSnapshot.info belongs to a different NodeInstance"
            )

    def _validate_alarm_scope(self) -> None:
        if self.alarms is None:
            return

        for alarm in self.alarms.alarms:
            if alarm.source != self.instance_id:
                raise ValueError(
                    "NodeSnapshot alarm belongs to a different "
                    "NodeInstance"
                )

            if not alarm.requires_attention:
                raise ValueError(
                    "NodeSnapshot must contain only active or "
                    "acknowledged alarms"
                )

    def _validate_heartbeat_scope(self) -> None:
        if self.heartbeat is None:
            return

        if (
            self.heartbeat.latest is not None
            and not self.heartbeat.belongs_to(self.instance_id)
        ):
            raise ValueError(
                "NodeSnapshot heartbeat belongs to a different "
                "NodeInstance"
            )

    @staticmethod
    def _validate_optional_type(
        value: object | None,
        expected_type: type,
        field_name: str,
    ) -> None:
        if value is not None and not isinstance(
            value,
            expected_type,
        ):
            raise TypeError(
                f"NodeSnapshot.{field_name} must be "
                f"{expected_type.__name__} or None"
            )

    @staticmethod
    def _validate_utc_datetime(
        value: datetime,
        field_name: str,
    ) -> None:
        if not isinstance(value, datetime):
            raise TypeError(
                f"NodeSnapshot.{field_name} must be a datetime"
            )

        if value.tzinfo is None:
            raise ValueError(
                f"NodeSnapshot.{field_name} must be "
                "timezone-aware and UTC"
            )

        offset = value.utcoffset()

        if offset is None or offset != timedelta(0):
            raise ValueError(
                f"NodeSnapshot.{field_name} must be expressed in UTC"
            )

    def __str__(self) -> str:
        return (
            f"{self.node_id}/{self.instance_id} "
            f"@ {self.snapshot_timestamp.isoformat()}"
        )
