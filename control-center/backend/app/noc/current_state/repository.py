"""Persistence ports for shared NOC current state.

ENG-013B — Current State

These protocols define storage-independent contracts for operational
state that must be shared across NOC processes.

Current state is distinct from durable operational history:

- it represents the latest known projection;
- newer values replace older values for the same NodeInstance;
- it is not immutable historical evidence;
- it may survive process restart so readers can expose the last known
  operational state.

Concrete adapters may use SQLite or another shared durable backend.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.noc.domain.node_health_diagnostic import (
    NodeHealthDiagnostic,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId


@runtime_checkable
class NodeHealthDiagnosticRepository(Protocol):
    """Shared current-state repository for Node health diagnostics."""

    def save(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        diagnostic: NodeHealthDiagnostic,
    ) -> None:
        """Create or replace the latest diagnostic for one NodeInstance."""
        ...

    def latest(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> NodeHealthDiagnostic | None:
        """Return the latest known diagnostic for one NodeInstance."""
        ...
