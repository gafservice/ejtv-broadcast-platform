"""Node Registry for the NOC Core.

ENG-013B — Node SDK

The registry manages logical Node registration and lookup while
delegating persistence to the NodeRepository port.

It contains no database, transport or infrastructure logic.
"""

from __future__ import annotations

from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId
from app.noc.registry.repository import NodeRepository


class NodeRegistryError(Exception):
    """Base exception for NodeRegistry operations."""


class NodeAlreadyRegisteredError(NodeRegistryError):
    """Raised when a NodeId is already registered."""


class NodeIdentityConflictError(NodeRegistryError):
    """Raised when the same NodeId is reused with conflicting identity."""


class NodeNotFoundError(NodeRegistryError):
    """Raised when a required Node is not registered."""


class NodeRegistry:
    """Application service that manages logical Node registration.

    NodeRegistry works exclusively through the NodeRepository port.

    Responsibilities:
    - register logical Nodes;
    - preserve NodeId and NodeType identity;
    - query registered Nodes;
    - explicitly retire Nodes.

    It does not:
    - manage transport;
    - persist snapshots;
    - manage NodeInstance lifecycle;
    - calculate operational state;
    - implement storage technology.
    """

    def __init__(
        self,
        repository: NodeRepository,
    ) -> None:
        if not isinstance(repository, NodeRepository):
            raise TypeError(
                "repository must implement NodeRepository"
            )

        self._repository = repository

    @property
    def repository(self) -> NodeRepository:
        """Return the persistence port used by the registry."""
        return self._repository

    def register(
        self,
        node: Node,
    ) -> Node:
        """Register a new logical Node.

        Registration is explicit. A NodeId may only represent one
        logical Node.

        Re-registering an existing NodeId is rejected. If the incoming
        NodeType differs from the registered NodeType, the condition is
        reported as an identity conflict.
        """
        self._require_node(node)

        existing = self._repository.get(
            node.node_id
        )

        if existing is not None:
            if existing.node_type is not node.node_type:
                raise NodeIdentityConflictError(
                    "NodeId "
                    f"{node.node_id.id!r} is already registered "
                    f"as NodeType {existing.node_type.value}; "
                    f"cannot register it as "
                    f"{node.node_type.value}"
                )

            raise NodeAlreadyRegisteredError(
                f"Node {node.node_id.id!r} is already registered"
            )

        self._repository.save(node)

        return node

    def get(
        self,
        node_id: NodeId,
    ) -> Node | None:
        """Return a registered Node or None."""
        self._require_node_id(node_id)

        return self._repository.get(
            node_id
        )

    def require(
        self,
        node_id: NodeId,
    ) -> Node:
        """Return a registered Node or raise NodeNotFoundError."""
        self._require_node_id(node_id)

        node = self._repository.get(
            node_id
        )

        if node is None:
            raise NodeNotFoundError(
                f"Node {node_id.id!r} is not registered"
            )

        return node

    def is_registered(
        self,
        node_id: NodeId,
    ) -> bool:
        """Return whether the logical Node is registered."""
        self._require_node_id(node_id)

        return self._repository.exists(
            node_id
        )

    def list_nodes(
        self,
    ) -> tuple[Node, ...]:
        """Return all registered Nodes in deterministic NodeId order."""
        nodes = self._repository.list_all()

        return tuple(
            sorted(
                nodes,
                key=lambda node: node.node_id.id,
            )
        )

    def retire(
        self,
        node_id: NodeId,
    ) -> Node:
        """Explicitly remove a logical Node from the registry.

        A Node is never retired merely because it currently has no
        active NodeInstances. Retirement must be explicit.
        """
        self._require_node_id(node_id)

        node = self._repository.get(
            node_id
        )

        if node is None:
            raise NodeNotFoundError(
                f"Node {node_id.id!r} is not registered"
            )

        removed = self._repository.delete(
            node_id
        )

        if not removed:
            raise NodeNotFoundError(
                f"Node {node_id.id!r} disappeared during retirement"
            )

        return node

    def count(
        self,
    ) -> int:
        """Return number of registered logical Nodes."""
        return self._repository.count()

    def __len__(self) -> int:
        return self.count()

    def __contains__(
        self,
        node_id: object,
    ) -> bool:
        if not isinstance(node_id, NodeId):
            return False

        return self.is_registered(
            node_id
        )

    @staticmethod
    def _require_node(
        node: Node,
    ) -> None:
        if not isinstance(node, Node):
            raise TypeError(
                "node must be a Node"
            )

    @staticmethod
    def _require_node_id(
        node_id: NodeId,
    ) -> None:
        if not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId"
            )
