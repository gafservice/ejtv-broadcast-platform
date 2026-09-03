"""Managed-history authority for durable NOC history.

ENG-013B — persistent operational history.

This port records the first UTC day for which one NodeInstance is
considered under durable history management.

Unlike observable historical range discovery, this anchor must not move
forward when retention removes old operational-history rows.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol, runtime_checkable

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId


@runtime_checkable
class ManagedHistoryRepository(Protocol):
    """Persist the managed-history lower bound for one NodeInstance."""

    def get_managed_since_day(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> date | None:
        """Return the first managed UTC day, if one has been established."""
        ...

    def ensure_managed_since_day(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        day: date,
        created_at: datetime,
    ) -> date:
        """Create the anchor once and return its durable value."""
        ...
