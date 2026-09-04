"""Policy service for safe durable NOC history retention.

ENG-013B — Operational History

The service decides whether durable SQLite history is eligible for
retention. The repository performs the transactional deletion.

Retention is fail-closed: every managed UTC day that would leave the
durable history must have valid sealed evidence before pruning is
allowed.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.evidence_day_sealer import (
    EvidenceDaySealer,
)
from app.noc.history.history_retention_repository import (
    HistoryRetentionRepository,
    HistoryRetentionResult,
)
from app.noc.history.managed_history_repository import (
    ManagedHistoryRepository,
)


class HistoryRetentionBlockedError(RuntimeError):
    """Raised when retention cannot safely remove durable history."""


class HistoryRetentionService:
    """Authorize retention only when historical evidence is complete."""

    def __init__(
        self,
        *,
        retention_repository: HistoryRetentionRepository,
        managed_history_repository: ManagedHistoryRepository,
        evidence_day_sealer: EvidenceDaySealer,
    ) -> None:
        if not isinstance(
            retention_repository,
            HistoryRetentionRepository,
        ):
            raise TypeError(
                "retention_repository must satisfy "
                "HistoryRetentionRepository"
            )

        if not isinstance(
            managed_history_repository,
            ManagedHistoryRepository,
        ):
            raise TypeError(
                "managed_history_repository must satisfy "
                "ManagedHistoryRepository"
            )

        if not isinstance(
            evidence_day_sealer,
            EvidenceDaySealer,
        ):
            raise TypeError(
                "evidence_day_sealer must be an "
                "EvidenceDaySealer"
            )

        self._retention_repository = retention_repository
        self._managed_history_repository = (
            managed_history_repository
        )
        self._evidence_day_sealer = evidence_day_sealer

    def prune_before(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        cutoff: datetime,
    ) -> HistoryRetentionResult:
        self._validate_cutoff(cutoff)

        first_day = (
            self._managed_history_repository
            .get_managed_since_day(
                node_id=node_id,
                instance_id=instance_id,
            )
        )

        if first_day is None:
            return HistoryRetentionResult(
                events_deleted=0,
                alarm_transitions_deleted=0,
                alarms_deleted=0,
            )

        cutoff_day = cutoff.date()

        if first_day >= cutoff_day:
            return HistoryRetentionResult(
                events_deleted=0,
                alarm_transitions_deleted=0,
                alarms_deleted=0,
            )

        day = first_day

        while day < cutoff_day:
            if not self._evidence_day_sealer.verify_day(
                day
            ):
                raise HistoryRetentionBlockedError(
                    "retention blocked because evidence "
                    f"for {day.isoformat()} is not valid and sealed"
                )

            day += timedelta(days=1)

        return self._retention_repository.prune_before(
            node_id=node_id,
            instance_id=instance_id,
            cutoff=cutoff,
        )

    @staticmethod
    def _validate_cutoff(
        cutoff: datetime,
    ) -> None:
        if not isinstance(cutoff, datetime):
            raise TypeError(
                "cutoff must be a datetime"
            )

        if (
            cutoff.tzinfo is None
            or cutoff.utcoffset() is None
        ):
            raise ValueError(
                "cutoff must be timezone-aware"
            )

        if cutoff.utcoffset().total_seconds() != 0:
            raise ValueError(
                "cutoff must be expressed in UTC"
            )

        midnight = datetime.combine(
            cutoff.date(),
            time.min,
            tzinfo=timezone.utc,
        )

        if cutoff != midnight:
            raise ValueError(
                "cutoff must be aligned to a UTC day boundary"
            )
