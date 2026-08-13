"""Heartbeat coordination service for the NOC.

ENG-013B — Node SDK
NCS reference: 19-NODE-HEARTBEAT.md

HeartbeatService coordinates reception of HeartbeatRecord objects for
registered NodeInstances.

It does not derive NodeStatus, NodeHealth, NodeAvailability or alarms.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.noc.domain.node_heartbeat import (
    HeartbeatRecord,
    NodeHeartbeat,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import (
    NodeInstance,
    NodeInstanceId,
)
from app.noc.registry.registry import (
    NodeNotFoundError,
    NodeRegistry,
)


class HeartbeatServiceError(Exception):
    """Base exception for HeartbeatService operations."""


class NodeInstanceNotFoundError(HeartbeatServiceError):
    """Raised when the Heartbeat targets an unknown NodeInstance."""


class HeartbeatInstanceMismatchError(HeartbeatServiceError):
    """Raised when record.instance_id does not match the target instance."""


class HeartbeatDisposition(str, Enum):
    """Classification of an accepted Heartbeat reception."""

    FIRST = "FIRST"
    CONTIGUOUS = "CONTIGUOUS"
    GAP = "GAP"
    RESTART = "RESTART"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class HeartbeatReceipt:
    """Result of processing an accepted HeartbeatRecord."""

    disposition: HeartbeatDisposition
    heartbeat: NodeHeartbeat
    previous: HeartbeatRecord | None = None
    missing_sequences: int = 0

    @property
    def record(self) -> HeartbeatRecord:
        """Return the newly accepted HeartbeatRecord."""
        assert self.heartbeat.latest is not None
        return self.heartbeat.latest

    @property
    def detected_gap(self) -> bool:
        return self.disposition is HeartbeatDisposition.GAP

    @property
    def detected_restart(self) -> bool:
        return self.disposition is HeartbeatDisposition.RESTART


class HeartbeatRejectedError(HeartbeatServiceError):
    """Base exception for Heartbeats that cannot replace the latest one."""


class DuplicateHeartbeatError(HeartbeatRejectedError):
    """Raised when a duplicate Heartbeat is received."""


class OutOfOrderHeartbeatError(HeartbeatRejectedError):
    """Raised when an older Heartbeat is received."""


class HeartbeatService:
    """Coordinate Heartbeat reception for registered NodeInstances.

    Rules implemented here:

    - the logical Node must already be registered;
    - the NodeInstance must belong to that Node;
    - HeartbeatRecord.instance_id must match that NodeInstance;
    - only the latest accepted Heartbeat is retained;
    - duplicate and out-of-order Heartbeats are rejected;
    - sequence gaps are reported without synthesizing alarms;
    - a later Heartbeat with reduced uptime is treated as a restart.

    The service deliberately does not infer NodeStatus, NodeHealth,
    NodeAvailability or Alarm state.
    """

    def __init__(
        self,
        registry: NodeRegistry,
    ) -> None:
        if not isinstance(registry, NodeRegistry):
            raise TypeError(
                "registry must be a NodeRegistry"
            )

        self._registry = registry

    @property
    def registry(self) -> NodeRegistry:
        return self._registry

    def receive(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        record: HeartbeatRecord,
    ) -> HeartbeatReceipt:
        """Accept the latest Heartbeat for one registered NodeInstance."""
        self._require_node_id(node_id)
        self._require_instance_id(instance_id)
        self._require_record(record)

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

        if record.instance_id != instance_id:
            raise HeartbeatInstanceMismatchError(
                "HeartbeatRecord.instance_id does not match "
                "the target NodeInstance"
            )

        previous = self._latest_record(
            instance
        )

        disposition, missing_sequences = (
            self._classify(
                previous,
                record,
            )
        )

        instance.heartbeat = NodeHeartbeat(
            latest=record
        )

        # Persist the changed aggregate through the repository port.
        self._registry.repository.save(
            node
        )

        return HeartbeatReceipt(
            disposition=disposition,
            heartbeat=instance.heartbeat,
            previous=previous,
            missing_sequences=missing_sequences,
        )

    def latest(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> NodeHeartbeat:
        """Return the latest known Heartbeat container for an instance."""
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

        heartbeat = getattr(
            instance,
            "heartbeat",
            None,
        )

        if isinstance(
            heartbeat,
            NodeHeartbeat,
        ):
            return heartbeat

        return NodeHeartbeat()

    def is_present(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> bool:
        """Return whether at least one Heartbeat has been received."""
        return self.latest(
            node_id,
            instance_id,
        ).is_present

    @staticmethod
    def _classify(
        previous: HeartbeatRecord | None,
        incoming: HeartbeatRecord,
    ) -> tuple[HeartbeatDisposition, int]:
        if previous is None:
            return (
                HeartbeatDisposition.FIRST,
                0,
            )

        if incoming.heartbeat_id == previous.heartbeat_id:
            raise DuplicateHeartbeatError(
                f"Heartbeat {incoming.heartbeat_id!r} "
                "has already been received"
            )

        # A heartbeat emitted later with lower uptime indicates that
        # the execution restarted. In that case its sequence may begin
        # again and is not considered out of order.
        restarted = (
            incoming.timestamp > previous.timestamp
            and incoming.uptime < previous.uptime
        )

        if restarted:
            return (
                HeartbeatDisposition.RESTART,
                0,
            )

        if incoming.timestamp < previous.timestamp:
            raise OutOfOrderHeartbeatError(
                "Heartbeat timestamp precedes the latest "
                "accepted Heartbeat"
            )

        if incoming.sequence == previous.sequence:
            raise DuplicateHeartbeatError(
                f"Heartbeat sequence {incoming.sequence} "
                "has already been received"
            )

        if incoming.sequence < previous.sequence:
            raise OutOfOrderHeartbeatError(
                f"Heartbeat sequence {incoming.sequence} precedes "
                f"latest sequence {previous.sequence}"
            )

        difference = (
            incoming.sequence
            - previous.sequence
        )

        if difference == 1:
            return (
                HeartbeatDisposition.CONTIGUOUS,
                0,
            )

        return (
            HeartbeatDisposition.GAP,
            difference - 1,
        )

    @staticmethod
    def _latest_record(
        instance: NodeInstance,
    ) -> HeartbeatRecord | None:
        heartbeat = getattr(
            instance,
            "heartbeat",
            None,
        )

        if not isinstance(
            heartbeat,
            NodeHeartbeat,
        ):
            return None

        return heartbeat.latest

    @staticmethod
    def _find_instance(
        instances: tuple[NodeInstance, ...],
        instance_id: NodeInstanceId,
    ) -> NodeInstance | None:
        for instance in instances:
            if instance.instance_id == instance_id:
                return instance

        return None

    @staticmethod
    def _require_node_id(
        node_id: NodeId,
    ) -> None:
        if not isinstance(node_id, NodeId):
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
    def _require_record(
        record: HeartbeatRecord,
    ) -> None:
        if not isinstance(
            record,
            HeartbeatRecord,
        ):
            raise TypeError(
                "record must be a HeartbeatRecord"
            )
