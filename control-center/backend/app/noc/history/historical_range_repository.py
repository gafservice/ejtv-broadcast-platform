"""Historical range discovery for durable NOC history.

ENG-013B — persistent operational history.

This port discovers durable temporal boundaries across the historical
records that constitute primary operational evidence.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId


@runtime_checkable
class HistoricalRangeRepository(Protocol):
    """Discover durable historical boundaries for one NodeInstance."""

    def first_historical_timestamp(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> datetime | None:
        """Return the earliest durable evidence timestamp for the scope."""
        ...
