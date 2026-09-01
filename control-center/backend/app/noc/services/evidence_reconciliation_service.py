"""Reconcile durable SQLite history into JSONL evidence.

ENG-013B — persistent operational history.

SQLite is the authoritative operational store.  JSONL is a durable
evidence projection.  This service replays durable records through the
idempotent EvidenceWriter so missing evidence can be reconstructed after
a crash or interrupted write.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.evidence_writer import EvidenceWriter
from app.noc.history.repository import (
    AlarmHistoryRepository,
    EventHistoryRepository,
)


@dataclass(frozen=True, slots=True)
class EvidenceReconciliationResult:
    """Summary of one evidence reconciliation run."""

    events_replayed: int
    alarm_transitions_replayed: int


class EvidenceReconciliationService:
    """Replay durable operational history into JSONL evidence."""

    def __init__(
        self,
        *,
        event_repository: EventHistoryRepository,
        alarm_repository: AlarmHistoryRepository,
        evidence_writer: EvidenceWriter,
    ) -> None:
        if not isinstance(
            event_repository,
            EventHistoryRepository,
        ):
            raise TypeError(
                "event_repository must implement "
                "EventHistoryRepository"
            )

        if not isinstance(
            alarm_repository,
            AlarmHistoryRepository,
        ):
            raise TypeError(
                "alarm_repository must implement "
                "AlarmHistoryRepository"
            )

        if not isinstance(
            evidence_writer,
            EvidenceWriter,
        ):
            raise TypeError(
                "evidence_writer must implement EvidenceWriter"
            )

        self._event_repository = event_repository
        self._alarm_repository = alarm_repository
        self._evidence_writer = evidence_writer

    def reconcile_between(
        self,
        *,
        start: datetime,
        end: datetime,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
    ) -> EvidenceReconciliationResult:
        """Replay durable history from [start, end) into evidence."""

        events = self._event_repository.list_between(
            start,
            end,
            node_id=node_id,
            instance_id=instance_id,
        )

        transitions = (
            self._alarm_repository.list_transitions_between(
                start,
                end,
                node_id=node_id,
                instance_id=instance_id,
            )
        )

        for record in events:
            self._evidence_writer.append_event(record)

        for transition in transitions:
            self._evidence_writer.append_alarm_transition(
                transition
            )

        return EvidenceReconciliationResult(
            events_replayed=len(events),
            alarm_transitions_replayed=len(transitions),
        )
