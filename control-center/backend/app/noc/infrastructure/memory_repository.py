"""In-memory persistence adapter for NOC Node aggregates.

ENG-013B — Node SDK

This module provides a concrete NodeRepository implementation backed
by process memory.

It is intended for:
- initial runtime composition;
- development;
- integration tests;
- local deployments where durable persistence is not yet required.

The repository owns no domain or registry policy. It only stores and
retrieves Node aggregate roots.
"""

from __future__ import annotations

from threading import RLock

from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId
from app.noc.registry.repository import NodeRepository


class InMemoryNodeRepository:
    """Thread-safe in-memory implementation of NodeRepository.

    Nodes are indexed by the canonical textual value of NodeId.

    save() follows the NodeRepository contract and therefore behaves
    as create-or-replace for an already known identity.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._lock = RLock()

    def save(
        self,
        node: Node,
    ) -> None:
        """Create or replace a Node aggregate."""
        self._require_node(node)

        with self._lock:
            self._nodes[
                node.node_id.id
            ] = node

    def get(
        self,
        node_id: NodeId,
    ) -> Node | None:
        """Return a Node by identity or None."""
        self._require_node_id(node_id)

        with self._lock:
            return self._nodes.get(
                node_id.id
            )

    def exists(
        self,
        node_id: NodeId,
    ) -> bool:
        """Return whether a Node exists."""
        self._require_node_id(node_id)

        with self._lock:
            return (
                node_id.id
                in self._nodes
            )

    def list_all(
        self,
    ) -> tuple[Node, ...]:
        """Return all stored Nodes in deterministic NodeId order."""
        with self._lock:
            return tuple(
                self._nodes[key]
                for key in sorted(
                    self._nodes
                )
            )

    def delete(
        self,
        node_id: NodeId,
    ) -> bool:
        """Remove a Node and report whether it existed."""
        self._require_node_id(node_id)

        with self._lock:
            return (
                self._nodes.pop(
                    node_id.id,
                    None,
                )
                is not None
            )

    def count(
        self,
    ) -> int:
        """Return number of stored Nodes."""
        with self._lock:
            return len(
                self._nodes
            )

    def clear(
        self,
    ) -> None:
        """Remove all Nodes.

        This utility is intentionally adapter-specific and is useful
        for development/test runtime reset. It is not part of the
        NodeRepository port.
        """
        with self._lock:
            self._nodes.clear()

    @staticmethod
    def _require_node(
        node: Node,
    ) -> None:
        if not isinstance(
            node,
            Node,
        ):
            raise TypeError(
                "node must be a Node"
            )

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


# Structural verification for readers/type-checkers:
# InMemoryNodeRepository satisfies NodeRepository without requiring
# inheritance from the Protocol.
_repository_contract: type[NodeRepository] = NodeRepository
