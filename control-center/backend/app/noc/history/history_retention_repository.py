"""Port for durable NOC history retention.

ENG-013B — Operational History

Retention removes durable operational history that is older than an
explicit UTC cutoff while preserving lifecycle and managed-history
invariants.

This port does not decide retention policy, evidence eligibility,
backup policy, or the managed-history lower bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId


@dataclass(frozen=True, slots=True)
class HistoryRetentionResult:
    """Counts of durable historical records removed by one prune."""

    events_deleted: int
    alarm_transitions_deleted: int
    alarms_deleted: int

    def __post_init__(self) -> None:
        for field_name in (
            "events_deleted",
            "alarm_transitions_deleted",
            "alarms_deleted",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(
                    f"{field_name} must be an int"
                )

            if value < 0:
                raise ValueError(
                    f"{field_name} must not be negative"
                )


@runtime_checkable
class HistoryRetentionRepository(Protocol):
    """Persistence boundary for transactional history pruning."""

    def prune_before(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        cutoff: datetime,
    ) -> HistoryRetentionResult:
        """Remove eligible history strictly before a UTC cutoff."""
        ...
