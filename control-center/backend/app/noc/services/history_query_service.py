"""Read-only query service for durable NOC operational history.

ENG-013B — Operational History.

This service exposes storage-independent historical queries over the
durable event and alarm repositories. Repository records remain canonical;
the service only defines operational query windows and scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.alarm_transition import AlarmTransition
from app.noc.history.event_history_record import EventHistoryRecord
from app.noc.history.repository import (
    AlarmHistoryRepository,
    EventHistoryRepository,
)


@dataclass(frozen=True, slots=True)
class HistoryQueryResult:
    """Immutable result of one historical operational query."""

    start: datetime
    end: datetime
    events: tuple[EventHistoryRecord, ...]
    alarm_transitions: tuple[AlarmTransition, ...]


class HistoryQueryService:
    """Query durable NOC history without exposing storage details."""

    def __init__(
        self,
        *,
        event_repository: EventHistoryRepository,
        alarm_repository: AlarmHistoryRepository,
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

        self._event_repository = event_repository
        self._alarm_repository = alarm_repository

    @property
    def event_repository(self) -> EventHistoryRepository:
        return self._event_repository

    @property
    def alarm_repository(self) -> AlarmHistoryRepository:
        return self._alarm_repository

    def last_24_hours(
        self,
        *,
        now: datetime | None = None,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
    ) -> HistoryQueryResult:
        """Return durable operational history in the previous 24 hours."""

        end = self._utc_timestamp(
            now
            if now is not None
            else datetime.now(timezone.utc)
        )
        start = end - timedelta(hours=24)

        events = self._event_repository.list_between(
            start,
            end,
            node_id=node_id,
            instance_id=instance_id,
        )

        alarm_transitions = (
            self._alarm_repository.list_transitions_between(
                start,
                end,
                node_id=node_id,
                instance_id=instance_id,
            )
        )

        return HistoryQueryResult(
            start=start,
            end=end,
            events=events,
            alarm_transitions=alarm_transitions,
        )

    @staticmethod
    def _utc_timestamp(value: datetime) -> datetime:
        if not isinstance(value, datetime):
            raise TypeError(
                "now must be a datetime"
            )

        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "now must be timezone-aware and UTC"
            )

        normalized = value.astimezone(timezone.utc)

        if value.utcoffset() != timedelta(0):
            raise ValueError(
                "now must be expressed in UTC"
            )

        return normalized
