"""Durable historical representation of operational NOC events.

ENG-013B — Operational History

EventRecord remains the canonical operational domain fact.
EventHistoryRecord adds persistence metadata required by the
historical/evidence subsystem.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.noc.domain.node_event import EventRecord
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId


@dataclass(frozen=True, slots=True)
class EventHistoryRecord:
    """Immutable durable historical envelope for an EventRecord."""

    event: EventRecord
    node_id: NodeId
    instance_id: NodeInstanceId
    recorded_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.event, EventRecord):
            raise TypeError(
                "EventHistoryRecord.event must be an EventRecord"
            )

        if not isinstance(self.node_id, NodeId):
            raise TypeError(
                "EventHistoryRecord.node_id must be a NodeId"
            )

        if not isinstance(self.instance_id, NodeInstanceId):
            raise TypeError(
                "EventHistoryRecord.instance_id must be a NodeInstanceId"
            )

        if self.event.source != self.instance_id:
            raise ValueError(
                "EventHistoryRecord.instance_id must match "
                "EventRecord.source"
            )

        self._validate_utc_datetime(
            self.recorded_at,
            "recorded_at",
        )

    @property
    def event_id(self) -> str:
        return self.event.event_id

    @property
    def timestamp(self) -> datetime:
        return self.event.timestamp

    @staticmethod
    def _validate_utc_datetime(
        value: datetime,
        field_name: str,
    ) -> None:
        if not isinstance(value, datetime):
            raise TypeError(
                f"EventHistoryRecord.{field_name} must be a datetime"
            )

        if value.tzinfo is None:
            raise ValueError(
                f"EventHistoryRecord.{field_name} must be "
                "timezone-aware and UTC"
            )

        offset = value.utcoffset()

        if offset is None or offset != timedelta(0):
            raise ValueError(
                f"EventHistoryRecord.{field_name} must be expressed in UTC"
            )
