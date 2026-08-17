"""Health coordination service for the NOC.

ENG-013B — Node SDK
NCS reference: 12-NODE-HEALTH.md

HealthService coordinates publication of NodeHealth objects for
registered NodeInstances.

It does not evaluate health. Health evaluation belongs to policy
components such as HealthEvaluator.
"""

from __future__ import annotations

from app.noc.domain.node_health import NodeHealth
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import (
    NodeInstance,
    NodeInstanceId,
)
from app.noc.registry.registry import NodeRegistry


class HealthServiceError(Exception):
    """Base exception for HealthService operations."""


class NodeInstanceNotFoundError(HealthServiceError):
    """Raised when health targets an unknown NodeInstance."""


class HealthService:
    """Coordinate health publication for registered NodeInstances."""

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
        health: NodeHealth,
    ) -> NodeHealth:
        """Publish current health for one registered NodeInstance."""

        self._require_node_id(node_id)
        self._require_instance_id(instance_id)
        self._require_health(health)

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

        instance.health = health

        self._registry.repository.save(
            node
        )

        return health

    def current(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> NodeHealth | None:
        """Return current health for one registered NodeInstance."""

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

        health = getattr(
            instance,
            "health",
            None,
        )

        if isinstance(
            health,
            NodeHealth,
        ):
            return health

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
    def _require_health(
        health: NodeHealth,
    ) -> None:
        if not isinstance(
            health,
            NodeHealth,
        ):
            raise TypeError(
                "health must be a NodeHealth"
            )
