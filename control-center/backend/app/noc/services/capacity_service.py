"""Capacity coordination service for the NOC.

ENG-013B — Node SDK
NCS reference: 15-NODE-CAPACITY.md

CapacityService coordinates publication of NodeCapacity objects for
registered NodeInstances.

It does not calculate capacity. Capacity calculation belongs to
infrastructure/application providers that observe the actual system.
"""

from __future__ import annotations

from app.noc.domain.node_capacity import NodeCapacity
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import (
    NodeInstance,
    NodeInstanceId,
)
from app.noc.registry.registry import NodeRegistry


class CapacityServiceError(Exception):
    """Base exception for CapacityService operations."""


class NodeInstanceNotFoundError(CapacityServiceError):
    """Raised when capacity targets an unknown NodeInstance."""


class CapacityService:
    """Coordinate capacity publication for registered NodeInstances."""

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

    def publish(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        capacity: NodeCapacity,
    ) -> NodeCapacity:
        """Publish current capacity for one registered NodeInstance."""

        self._require_node_id(node_id)
        self._require_instance_id(instance_id)
        self._require_capacity(capacity)

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

        instance.capacity = capacity

        # Persist the changed aggregate through the repository port.
        self._registry.repository.save(
            node
        )

        return capacity

    def current(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> NodeCapacity | None:
        """Return current capacity for one registered NodeInstance."""

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

        capacity = getattr(
            instance,
            "capacity",
            None,
        )

        if isinstance(
            capacity,
            NodeCapacity,
        ):
            return capacity

        return None

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
    def _require_capacity(
        capacity: NodeCapacity,
    ) -> None:
        if not isinstance(
            capacity,
            NodeCapacity,
        ):
            raise TypeError(
                "capacity must be a NodeCapacity"
            )
