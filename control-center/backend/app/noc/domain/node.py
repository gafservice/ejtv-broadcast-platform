"""Aggregate Root for the NOC Node domain.

ENG-013B — Node SDK
NCS reference: 06-NODE.md
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstance, NodeInstanceId
from app.noc.domain.node_type import NodeType


@dataclass(slots=True)
class Node:
    """Logical Aggregate Root of the Node Contract domain.

    A Node represents a stable logical capability of the platform.
    Runtime execution is represented by NodeInstance objects.

    The Node owns the collection of instances and preserves the
    aggregate invariants defined by the Node Contract Specification.
    """

    node_id: NodeId
    node_type: NodeType
    _instances: dict[NodeInstanceId, NodeInstance] = field(
        default_factory=dict,
        repr=False,
    )

    def __post_init__(self) -> None:
        """Validate Aggregate Root invariants."""
        if not isinstance(self.node_id, NodeId):
            raise TypeError("Node.node_id must be a NodeId")

        if not isinstance(self.node_type, NodeType):
            raise TypeError("Node.node_type must be a NodeType")

        for instance_id, instance in self._instances.items():
            if not isinstance(instance_id, NodeInstanceId):
                raise TypeError(
                    "Node instance keys must be NodeInstanceId objects"
                )

            if not isinstance(instance, NodeInstance):
                raise TypeError(
                    "Node instances must be NodeInstance objects"
                )

            self._validate_instance_belongs_to_node(instance)

            if instance.instance_id != instance_id:
                raise ValueError(
                    "Node instance dictionary key does not match "
                    "NodeInstance.instance_id"
                )

    @property
    def instances(self) -> tuple[NodeInstance, ...]:
        """Return an immutable view of the registered instances."""
        return tuple(self._instances.values())

    @property
    def instance_count(self) -> int:
        """Return the number of registered instances."""
        return len(self._instances)

    def add_instance(self, instance: NodeInstance) -> None:
        """Add a NodeInstance to this aggregate.

        Raises:
            TypeError:
                If instance is not a NodeInstance.
            ValueError:
                If the instance belongs to another Node or if another
                instance with the same NodeInstanceId already exists.
        """
        if not isinstance(instance, NodeInstance):
            raise TypeError("instance must be a NodeInstance")

        self._validate_instance_belongs_to_node(instance)

        if instance.instance_id in self._instances:
            raise ValueError(
                f"NodeInstance already registered: {instance.instance_id}"
            )

        self._instances[instance.instance_id] = instance

    def remove_instance(
        self,
        instance_id: NodeInstanceId | str,
    ) -> NodeInstance:
        """Remove and return an instance from the Node.

        Removing the final instance does not remove or invalidate the
        logical Node.
        """
        normalized_id = self._normalize_instance_id(instance_id)

        try:
            return self._instances.pop(normalized_id)
        except KeyError as exc:
            raise KeyError(
                f"NodeInstance not registered: {normalized_id}"
            ) from exc

    def get_instance(
        self,
        instance_id: NodeInstanceId | str,
    ) -> NodeInstance | None:
        """Return a registered instance or None when it does not exist."""
        normalized_id = self._normalize_instance_id(instance_id)
        return self._instances.get(normalized_id)

    def has_instance(
        self,
        instance_id: NodeInstanceId | str,
    ) -> bool:
        """Return whether the Node contains the given instance."""
        normalized_id = self._normalize_instance_id(instance_id)
        return normalized_id in self._instances

    def create_instance(
        self,
        *,
        instance_id: str,
    ) -> NodeInstance:
        """Create and register a NodeInstance owned by this Node."""
        instance = NodeInstance.create(
            instance_id=instance_id,
            node_id=self.node_id,
        )
        self.add_instance(instance)
        return instance

    def _validate_instance_belongs_to_node(
        self,
        instance: NodeInstance,
    ) -> None:
        if instance.node_id != self.node_id:
            raise ValueError(
                "NodeInstance belongs to a different Node"
            )

    @staticmethod
    def _normalize_instance_id(
        instance_id: NodeInstanceId | str,
    ) -> NodeInstanceId:
        if isinstance(instance_id, NodeInstanceId):
            return instance_id

        if isinstance(instance_id, str):
            return NodeInstanceId(instance_id)

        raise TypeError(
            "instance_id must be NodeInstanceId or str"
        )

    def __len__(self) -> int:
        return self.instance_count

    def __contains__(
        self,
        instance_id: NodeInstanceId | str,
    ) -> bool:
        return self.has_instance(instance_id)

    def __str__(self) -> str:
        """Return the canonical Node identity."""
        return str(self.node_id)
