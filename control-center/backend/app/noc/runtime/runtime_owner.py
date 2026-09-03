"""Ownership contract for the operational NOC runtime.

A NodeInstance may have many readers and presentation clients, but only
one logical runtime owner is allowed to perform operational mutations.

The owner is responsible for coordinating operations such as:

- runtime bootstrap;
- telemetry refresh;
- event generation;
- alarm lifecycle mutations;
- alarm recovery;
- daily continuity;
- evidence reconciliation;
- evidence sealing;
- retention and backup.

Terminal and Web clients are readers of the NOC state.  Starting a
presentation client must not implicitly create another operational owner.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId


@dataclass(frozen=True, slots=True)
class RuntimeOwnerIdentity:
    """Logical identity of one operational NOC runtime owner."""

    node_id: NodeId
    instance_id: NodeInstanceId


class RuntimeOwnershipError(RuntimeError):
    """Raised when runtime ownership invariants are violated."""


class RuntimeOwner:
    """Represents the logical owner of one NodeInstance runtime.

    This first implementation deliberately models ownership only.

    Inter-process acquisition, leases and process locking are separate
    infrastructure concerns and will be introduced after the ownership
    contract is established and tested.
    """

    def __init__(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> None:
        self._identity = RuntimeOwnerIdentity(
            node_id=node_id,
            instance_id=instance_id,
        )

    @property
    def identity(self) -> RuntimeOwnerIdentity:
        """Return the Node/Instance identity owned by this runtime."""

        return self._identity

    @property
    def node_id(self) -> NodeId:
        """Return the owned Node identifier."""

        return self._identity.node_id

    @property
    def instance_id(self) -> NodeInstanceId:
        """Return the owned NodeInstance identifier."""

        return self._identity.instance_id
