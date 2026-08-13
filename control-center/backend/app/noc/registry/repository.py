"""Repository contract for NOC Node aggregates.

ENG-013B — Node SDK

This module defines the persistence port used by the Node Registry.
It contains no storage implementation and has no dependency on
databases, filesystems, caches or transport technologies.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId


@runtime_checkable
class NodeRepository(Protocol):
    """Persistence abstraction for Node aggregate roots.

    Implementations may use memory, SQL, Redis or another persistence
    mechanism without changing the Registry or domain layers.

    Repository operations are expressed entirely using domain types.
    """

    def save(
        self,
        node: Node,
    ) -> None:
        """Create or replace a Node aggregate.

        The implementation must preserve the canonical NodeId and
        the complete aggregate supplied by the caller.
        """
        ...

    def get(
        self,
        node_id: NodeId,
    ) -> Node | None:
        """Return a Node by canonical identity.

        Returns None when the Node is not present.
        """
        ...

    def exists(
        self,
        node_id: NodeId,
    ) -> bool:
        """Return whether a Node with this identity exists."""
        ...

    def list_all(
        self,
    ) -> tuple[Node, ...]:
        """Return all currently stored Node aggregates.

        The repository contract does not impose physical ordering.
        Concrete implementations should nevertheless provide
        deterministic results when practical.
        """
        ...

    def delete(
        self,
        node_id: NodeId,
    ) -> bool:
        """Remove a Node.

        Returns True when a Node was removed and False when the
        identity was not present.
        """
        ...

    def count(
        self,
    ) -> int:
        """Return the number of stored Node aggregates."""
        ...
