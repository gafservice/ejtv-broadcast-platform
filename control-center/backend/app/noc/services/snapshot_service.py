"""Snapshot construction service for the NOC.

ENG-013B — Node SDK
NCS reference: 20-NODE-SNAPSHOT.md

SnapshotService builds a coherent NodeSnapshot from a registered
NodeInstance using the operational dimensions currently available.

It does not invent missing information, serialize payloads or include
event history.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.noc.domain.node_alarm import (
    AlarmRecord,
    NodeAlarm,
)
from app.noc.domain.node_availability import NodeAvailability
from app.noc.domain.node_capacity import NodeCapacity
from app.noc.domain.node_capability import (
    CapabilityDefinition,
    NodeCapability,
)
from app.noc.domain.node_health import NodeHealth
from app.noc.domain.node_heartbeat import NodeHeartbeat
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_info import NodeInfo
from app.noc.domain.node_instance import (
    NodeInstance,
    NodeInstanceId,
)
from app.noc.domain.node_metric import (
    MetricSample,
    NodeMetric,
)
from app.noc.domain.node_snapshot import NodeSnapshot
from app.noc.domain.node_status import NodeStatus
from app.noc.registry.registry import NodeRegistry
from app.noc.services.heartbeat_service import (
    NodeInstanceNotFoundError,
)
from app.noc.validators.validator import (
    ContractValidator,
    ValidationResult,
)


class SnapshotServiceError(Exception):
    """Base exception for SnapshotService operations."""


class SnapshotValidationError(SnapshotServiceError):
    """Raised when a constructed Snapshot fails contract validation."""

    def __init__(
        self,
        result: ValidationResult,
    ) -> None:
        self.result = result

        super().__init__(
            "Constructed NodeSnapshot failed contract validation"
        )


class SnapshotService:
    """Build validated NodeSnapshot objects for registered instances.

    Responsibilities:
    - locate a registered Node and NodeInstance;
    - collect the current operational dimensions;
    - compose collection-backed instance data into canonical aggregates;
    - build an immutable NodeSnapshot;
    - validate the resulting contract.

    It does not:
    - serialize JSON;
    - persist Snapshot history;
    - infer missing operational values;
    - generate metrics, alarms or Heartbeats;
    - include NodeEvent history.
    """

    def __init__(
        self,
        registry: NodeRegistry,
        validator: ContractValidator | None = None,
    ) -> None:
        if not isinstance(registry, NodeRegistry):
            raise TypeError(
                "registry must be a NodeRegistry"
            )

        if (
            validator is not None
            and not isinstance(
                validator,
                ContractValidator,
            )
        ):
            raise TypeError(
                "validator must be a ContractValidator or None"
            )

        self._registry = registry
        self._validator = (
            validator
            or ContractValidator()
        )

    @property
    def registry(self) -> NodeRegistry:
        return self._registry

    @property
    def validator(self) -> ContractValidator:
        return self._validator

    def build(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        *,
        timestamp: datetime | None = None,
        validate: bool = True,
    ) -> NodeSnapshot:
        """Build a Snapshot from the current state of one NodeInstance."""
        self._require_node_id(node_id)
        self._require_instance_id(instance_id)

        node = self._registry.require(
            node_id
        )

        instance = self._find_instance(
            node.instances,
            instance_id,
        )

        if instance is None:
            raise NodeInstanceNotFoundError(
                f"NodeInstance {instance_id!s} is not registered "
                f"under Node {node_id.id!r}"
            )

        snapshot_timestamp = (
            timestamp
            if timestamp is not None
            else datetime.now(timezone.utc)
        )

        self._require_utc_datetime(
            snapshot_timestamp
        )

        snapshot = NodeSnapshot(
            node_id=node.node_id,
            node_type=node.node_type,
            instance_id=instance.instance_id,
            snapshot_timestamp=snapshot_timestamp,

            info=self._optional_component(
                instance,
                "info",
                NodeInfo,
            ),

            status=self._optional_component(
                instance,
                "status",
                NodeStatus,
            ),

            health=self._optional_component(
                instance,
                "health",
                NodeHealth,
            ),

            availability=self._optional_component(
                instance,
                "availability",
                NodeAvailability,
            ),

            capability=self._extract_capabilities(
                instance
            ),

            capacity=self._optional_component(
                instance,
                "capacity",
                NodeCapacity,
            ),

            metric=self._extract_metrics(
                instance
            ),

            alarms=self._extract_alarms(
                instance
            ),

            heartbeat=self._optional_component(
                instance,
                "heartbeat",
                NodeHeartbeat,
            ),
        )

        if validate:
            result = (
                self._validator
                .validate_snapshot(snapshot)
            )

            if not result.is_valid:
                raise SnapshotValidationError(
                    result
                )

        instance.snapshot = snapshot

        # Persist the changed aggregate through the repository port.
        self._registry.repository.save(
            node
        )

        return snapshot

    def latest(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> NodeSnapshot | None:
        """Return the last Snapshot stored on the NodeInstance."""
        self._require_node_id(node_id)
        self._require_instance_id(instance_id)

        node = self._registry.require(
            node_id
        )

        instance = self._find_instance(
            node.instances,
            instance_id,
        )

        if instance is None:
            raise NodeInstanceNotFoundError(
                f"NodeInstance {instance_id!s} is not registered "
                f"under Node {node_id.id!r}"
            )

        snapshot = getattr(
            instance,
            "snapshot",
            None,
        )

        if snapshot is None:
            return None

        if not isinstance(
            snapshot,
            NodeSnapshot,
        ):
            raise SnapshotServiceError(
                "NodeInstance.snapshot contains an invalid value"
            )

        return snapshot

    @staticmethod
    def _extract_capabilities(
        instance: NodeInstance,
    ) -> NodeCapability | None:
        """Compose NodeInstance capabilities into NodeCapability."""
        value = getattr(
            instance,
            "capabilities",
            (),
        )

        if value is None:
            return None

        # Defensive compatibility if an aggregate is assigned directly.
        if isinstance(
            value,
            NodeCapability,
        ):
            return value

        if not isinstance(
            value,
            tuple,
        ):
            raise SnapshotServiceError(
                "NodeInstance.capabilities must be a tuple "
                "or NodeCapability"
            )

        if not value:
            return None

        definitions: list[
            CapabilityDefinition
        ] = []

        for item in value:
            if isinstance(
                item,
                NodeCapability,
            ):
                definitions.extend(
                    item.capabilities
                )

            elif isinstance(
                item,
                CapabilityDefinition,
            ):
                definitions.append(
                    item
                )

            else:
                raise SnapshotServiceError(
                    "NodeInstance.capabilities must contain "
                    "NodeCapability or CapabilityDefinition objects"
                )

        if not definitions:
            return None

        return NodeCapability(
            capabilities=tuple(
                definitions
            )
        )

    @staticmethod
    def _extract_metrics(
        instance: NodeInstance,
    ) -> NodeMetric | None:
        """Compose NodeInstance metrics into one NodeMetric."""
        value = getattr(
            instance,
            "metrics",
            (),
        )

        if value is None:
            return None

        if isinstance(
            value,
            NodeMetric,
        ):
            return value

        if not isinstance(
            value,
            tuple,
        ):
            raise SnapshotServiceError(
                "NodeInstance.metrics must be a tuple "
                "or NodeMetric"
            )

        if not value:
            return None

        samples: list[
            MetricSample
        ] = []

        for item in value:
            if isinstance(
                item,
                NodeMetric,
            ):
                samples.extend(
                    item.samples
                )

            elif isinstance(
                item,
                MetricSample,
            ):
                samples.append(
                    item
                )

            else:
                raise SnapshotServiceError(
                    "NodeInstance.metrics must contain "
                    "NodeMetric or MetricSample objects"
                )

        if not samples:
            return None

        return NodeMetric(
            samples=tuple(samples)
        )

    @staticmethod
    def _extract_alarms(
        instance: NodeInstance,
    ) -> NodeAlarm | None:
        """Compose active instance alarms into one NodeAlarm.

        Snapshot represents current state, therefore alarms that no
        longer require attention are intentionally excluded.
        """
        value = getattr(
            instance,
            "alarms",
            (),
        )

        if value is None:
            return None

        if isinstance(
            value,
            NodeAlarm,
        ):
            records = list(
                value.alarms
            )

        elif isinstance(
            value,
            tuple,
        ):
            if not value:
                return None

            records: list[
                AlarmRecord
            ] = []

            for item in value:
                if isinstance(
                    item,
                    NodeAlarm,
                ):
                    records.extend(
                        item.alarms
                    )

                elif isinstance(
                    item,
                    AlarmRecord,
                ):
                    records.append(
                        item
                    )

                else:
                    raise SnapshotServiceError(
                        "NodeInstance.alarms must contain "
                        "NodeAlarm or AlarmRecord objects"
                    )

        else:
            raise SnapshotServiceError(
                "NodeInstance.alarms must be a tuple "
                "or NodeAlarm"
            )

        active_records = tuple(
            alarm
            for alarm in records
            if alarm.requires_attention
        )

        if not active_records:
            return None

        return NodeAlarm(
            alarms=active_records
        )

    @staticmethod
    def _optional_component(
        instance: NodeInstance,
        attribute: str,
        expected_type: type,
    ):
        value = getattr(
            instance,
            attribute,
            None,
        )

        if value is None:
            return None

        if not isinstance(
            value,
            expected_type,
        ):
            raise SnapshotServiceError(
                f"NodeInstance.{attribute} must be "
                f"{expected_type.__name__}"
            )

        return value

    @staticmethod
    def _find_instance(
        instances: tuple[NodeInstance, ...],
        instance_id: NodeInstanceId,
    ) -> NodeInstance | None:
        for instance in instances:
            if (
                instance.instance_id
                == instance_id
            ):
                return instance

        return None

    @staticmethod
    def _require_node_id(
        node_id: NodeId,
    ) -> None:
        if not isinstance(
            node_id,
            NodeId,
        ):
            raise TypeError(
                "node_id must be a NodeId"
            )

    @staticmethod
    def _require_instance_id(
        instance_id: NodeInstanceId,
    ) -> None:
        if not isinstance(
            instance_id,
            NodeInstanceId,
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

    @staticmethod
    def _require_utc_datetime(
        value: datetime,
    ) -> None:
        if not isinstance(
            value,
            datetime,
        ):
            raise TypeError(
                "timestamp must be a datetime"
            )

        if value.tzinfo is None:
            raise ValueError(
                "timestamp must be timezone-aware and UTC"
            )

        offset = value.utcoffset()

        if (
            offset is None
            or offset.total_seconds() != 0
        ):
            raise ValueError(
                "timestamp must be expressed in UTC"
            )
