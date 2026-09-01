"""Persistence ports for durable NOC operational history.

ENG-013B — Operational History

These protocols define storage-independent contracts for:
- immutable operational event history;
- alarm lifecycle history and recovery.

Concrete adapters may use SQLite or another durable backend.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from app.noc.domain.node_alarm import AlarmRecord
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.alarm_transition import AlarmTransition
from app.noc.history.event_history_record import EventHistoryRecord


@runtime_checkable
class EventHistoryRepository(Protocol):
    """Durable repository contract for operational events."""

    def append(
        self,
        record: EventHistoryRecord,
    ) -> None:
        """Persist one immutable event history record."""
        ...

    def get(
        self,
        event_id: str,
    ) -> EventHistoryRecord | None:
        """Return one historical event by canonical event id."""
        ...

    def list_between(
        self,
        start: datetime,
        end: datetime,
        *,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
    ) -> tuple[EventHistoryRecord, ...]:
        """Return events whose event timestamp falls in [start, end)."""
        ...


@runtime_checkable
class AlarmHistoryRepository(Protocol):
    """Durable repository contract for alarm state and lifecycle."""

    def save_current(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        alarm: AlarmRecord,
    ) -> None:
        """Create or replace the current canonical state of an alarm."""
        ...

    def append_transition(
        self,
        transition: AlarmTransition,
    ) -> None:
        """Persist one immutable alarm lifecycle transition."""
        ...

    def record_lifecycle(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        alarm: AlarmRecord,
        transition: AlarmTransition,
    ) -> None:
        """Atomically persist current alarm state and its transition."""
        ...

    def get_current(
        self,
        alarm_id: str,
    ) -> AlarmRecord | None:
        """Return the current canonical alarm state."""
        ...

    def list_all(
        self,
        *,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
    ) -> tuple[AlarmRecord, ...]:
        """Return all current alarm records in the requested scope."""
        ...

    def record_historical_transition(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        transition: AlarmTransition,
    ) -> None:
        """Persist an immutable transition without changing current state.

        Exact retries of the same transition are idempotent. Reusing the
        same transition_id with different data is a conflict.
        """
        ...

    def list_active(
        self,
        *,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
    ) -> tuple[AlarmRecord, ...]:
        """Return alarms that still require operational attention."""
        ...

    def list_transitions(
        self,
        alarm_id: str,
    ) -> tuple[AlarmTransition, ...]:
        """Return the complete lifecycle history of one alarm."""
        ...

    def list_transitions_between(
        self,
        start: datetime,
        end: datetime,
        *,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
    ) -> tuple[AlarmTransition, ...]:
        """Return transitions whose timestamps fall in [start, end)."""
        ...
