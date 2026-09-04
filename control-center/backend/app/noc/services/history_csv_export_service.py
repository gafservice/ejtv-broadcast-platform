"""Service for exporting durable NOC history as canonical CSV.

ENG-013B — Operational History.

This service coordinates arbitrary half-open history queries [start, end),
canonical CSV serialization, and publication through the CSV export port.

It does not own historical persistence, evidence sealing, retention,
backup, or runtime lifecycle.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.csv_export import (
    serialize_alarm_transition_csv,
    serialize_event_csv,
)
from app.noc.history.csv_export_repository import (
    CsvExportRepository,
    CsvExportResult,
)
from app.noc.history.repository import (
    AlarmHistoryRepository,
    EventHistoryRepository,
)


class HistoryCsvExportService:
    """Export one durable history range as canonical CSV."""

    def __init__(
        self,
        *,
        event_repository: EventHistoryRepository,
        alarm_repository: AlarmHistoryRepository,
        export_repository: CsvExportRepository,
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
            export_repository,
            CsvExportRepository,
        ):
            raise TypeError(
                "export_repository must implement "
                "CsvExportRepository"
            )

        self._event_repository = event_repository
        self._alarm_repository = alarm_repository
        self._export_repository = export_repository

    def export_range(
        self,
        *,
        start: datetime,
        end: datetime,
        destination: Path,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
    ) -> CsvExportResult:
        """Export durable history whose timestamps fall in [start, end)."""

        normalized_start = self._utc_timestamp(
            start,
            name="start",
        )
        normalized_end = self._utc_timestamp(
            end,
            name="end",
        )

        if normalized_start >= normalized_end:
            raise ValueError(
                "start must be earlier than end"
            )

        if not isinstance(
            destination,
            Path,
        ):
            raise TypeError(
                "destination must be a Path"
            )

        if (
            node_id is not None
            and not isinstance(node_id, NodeId)
        ):
            raise TypeError(
                "node_id must be a NodeId or None"
            )

        if (
            instance_id is not None
            and not isinstance(
                instance_id,
                NodeInstanceId,
            )
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId or None"
            )

        events = (
            self._event_repository.list_between(
                normalized_start,
                normalized_end,
                node_id=node_id,
                instance_id=instance_id,
            )
        )

        alarm_transitions = (
            self._alarm_repository.list_transitions_between(
                normalized_start,
                normalized_end,
                node_id=node_id,
                instance_id=instance_id,
            )
        )

        events_csv = serialize_event_csv(
            events
        )

        alarm_transitions_csv = (
            serialize_alarm_transition_csv(
                alarm_transitions
            )
        )

        return self._export_repository.publish(
            destination=destination,
            events_csv=events_csv,
            alarm_transitions_csv=(
                alarm_transitions_csv
            ),
        )

    @staticmethod
    def _utc_timestamp(
        value: datetime,
        *,
        name: str,
    ) -> datetime:
        if not isinstance(
            value,
            datetime,
        ):
            raise TypeError(
                f"{name} must be a datetime"
            )

        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                f"{name} must be timezone-aware and UTC"
            )

        if (
            value.utcoffset()
            != timedelta(0)
        ):
            raise ValueError(
                f"{name} must be expressed in UTC"
            )

        return value.astimezone(
            timezone.utc
        )
