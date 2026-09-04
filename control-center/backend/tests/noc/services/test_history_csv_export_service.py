"""Tests for durable NOC history CSV export coordination."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.history.alarm_transition import (
    AlarmTransition,
    AlarmTransitionType,
    make_alarm_transition_id,
)
from app.noc.history.csv_export_repository import (
    CsvExportResult,
)
from app.noc.history.event_history_record import (
    EventHistoryRecord,
)
from app.noc.history.memory_repository import (
    InMemoryAlarmHistoryRepository,
    InMemoryEventHistoryRepository,
)
from app.noc.services.history_csv_export_service import (
    HistoryCsvExportService,
)


NOW = datetime(
    2026,
    9,
    4,
    18,
    0,
    tzinfo=timezone.utc,
)


class CapturingCsvExportRepository:
    def __init__(self) -> None:
        self.calls = []

    def publish(
        self,
        *,
        destination,
        events_csv,
        alarm_transitions_csv,
    ):
        self.calls.append(
            (
                destination,
                events_csv,
                alarm_transitions_csv,
            )
        )

        return CsvExportResult(
            path=destination,
            events_file=(
                destination
                / "events.csv"
            ),
            alarm_transitions_file=(
                destination
                / "alarm_transitions.csv"
            ),
        )


def make_context():
    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
            created_at=NOW - timedelta(days=30),
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    events = InMemoryEventHistoryRepository()
    alarms = InMemoryAlarmHistoryRepository()
    exporter = CapturingCsvExportRepository()

    service = HistoryCsvExportService(
        event_repository=events,
        alarm_repository=alarms,
        export_repository=exporter,
    )

    return (
        node,
        instance,
        events,
        alarms,
        exporter,
        service,
    )


def persist_event(
    events,
    node,
    instance,
    *,
    event_id,
    timestamp,
):
    event = EventRecord(
        event_id=event_id,
        event_type="TEST_EVENT",
        severity=EventSeverity.INFO,
        timestamp=timestamp,
        source=instance.instance_id,
        title="Test event",
        description="Historical test event",
    )

    record = EventHistoryRecord(
        event=event,
        node_id=node.node_id,
        instance_id=instance.instance_id,
        recorded_at=timestamp,
    )

    events.append(
        record
    )

    return record


def persist_alarm_transition(
    alarms,
    node,
    instance,
    *,
    alarm_id,
    timestamp,
):
    alarm = AlarmRecord(
        alarm_id=alarm_id,
        alarm_type="TEST_ALARM",
        severity=AlarmSeverity.CRITICAL,
        state=AlarmState.ACTIVE,
        timestamp=timestamp,
        source=instance.instance_id,
        title="Test alarm",
        description="Historical test alarm",
    )

    transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=alarm.alarm_id,
            transition_type=AlarmTransitionType.OPENED,
            timestamp=timestamp,
            source=instance.instance_id,
            state=alarm.state,
        ),
        alarm_id=alarm.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=timestamp,
        source=instance.instance_id,
        state=alarm.state,
    )

    alarms.record_lifecycle(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        alarm=alarm,
        transition=transition,
    )

    return transition


def _rows(document):
    return list(
        csv.DictReader(
            io.StringIO(document)
        )
    )


def test_export_range_serializes_requested_history():
    (
        node,
        instance,
        events,
        alarms,
        exporter,
        service,
    ) = make_context()

    persist_event(
        events,
        node,
        instance,
        event_id="event-inside",
        timestamp=NOW - timedelta(hours=2),
    )

    persist_alarm_transition(
        alarms,
        node,
        instance,
        alarm_id="alarm-inside",
        timestamp=NOW - timedelta(hours=1),
    )

    result = service.export_range(
        start=NOW - timedelta(hours=3),
        end=NOW,
        destination=Path("/tmp/export"),
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert result.path == Path(
        "/tmp/export"
    )

    assert len(exporter.calls) == 1

    (
        destination,
        events_csv,
        alarms_csv,
    ) = exporter.calls[0]

    assert destination == Path(
        "/tmp/export"
    )

    assert [
        row["event_id"]
        for row in _rows(events_csv)
    ] == [
        "event-inside"
    ]

    assert [
        row["alarm_id"]
        for row in _rows(alarms_csv)
    ] == [
        "alarm-inside"
    ]


def test_export_range_uses_half_open_window():
    (
        node,
        instance,
        events,
        _,
        exporter,
        service,
    ) = make_context()

    start = NOW - timedelta(hours=2)
    end = NOW

    persist_event(
        events,
        node,
        instance,
        event_id="event-at-start",
        timestamp=start,
    )

    persist_event(
        events,
        node,
        instance,
        event_id="event-at-end",
        timestamp=end,
    )

    service.export_range(
        start=start,
        end=end,
        destination=Path("/tmp/export"),
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    rows = _rows(
        exporter.calls[0][1]
    )

    assert [
        row["event_id"]
        for row in rows
    ] == [
        "event-at-start"
    ]


def test_export_range_respects_scope():
    (
        node,
        instance,
        events,
        _,
        exporter,
        service,
    ) = make_context()

    other_instance = node.create_instance(
        instance_id="streaming-secondary"
    )

    persist_event(
        events,
        node,
        instance,
        event_id="event-primary",
        timestamp=NOW - timedelta(minutes=20),
    )

    persist_event(
        events,
        node,
        other_instance,
        event_id="event-secondary",
        timestamp=NOW - timedelta(minutes=10),
    )

    service.export_range(
        start=NOW - timedelta(hours=1),
        end=NOW,
        destination=Path("/tmp/export"),
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    rows = _rows(
        exporter.calls[0][1]
    )

    assert [
        row["event_id"]
        for row in rows
    ] == [
        "event-primary"
    ]


def test_export_empty_range_still_publishes_headers():
    (
        node,
        instance,
        _,
        _,
        exporter,
        service,
    ) = make_context()

    service.export_range(
        start=NOW - timedelta(hours=1),
        end=NOW,
        destination=Path("/tmp/export"),
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert _rows(
        exporter.calls[0][1]
    ) == []

    assert _rows(
        exporter.calls[0][2]
    ) == []


@pytest.mark.parametrize(
    (
        "start",
        "end",
        "message",
    ),
    (
        (
            NOW,
            NOW,
            "start must be earlier than end",
        ),
        (
            NOW,
            NOW - timedelta(seconds=1),
            "start must be earlier than end",
        ),
    ),
)
def test_export_range_rejects_invalid_window(
    start,
    end,
    message,
):
    *_, service = make_context()

    with pytest.raises(
        ValueError,
        match=message,
    ):
        service.export_range(
            start=start,
            end=end,
            destination=Path("/tmp/export"),
        )


def test_export_range_requires_utc_boundaries():
    *_, service = make_context()

    with pytest.raises(
        ValueError,
        match="start.*UTC",
    ):
        service.export_range(
            start=datetime(
                2026,
                9,
                4,
                17,
                0,
            ),
            end=NOW,
            destination=Path("/tmp/export"),
        )

    offset = timezone(
        timedelta(hours=-6)
    )

    with pytest.raises(
        ValueError,
        match="end.*UTC",
    ):
        service.export_range(
            start=NOW - timedelta(hours=1),
            end=datetime(
                2026,
                9,
                4,
                12,
                0,
                tzinfo=offset,
            ),
            destination=Path("/tmp/export"),
        )


def test_export_range_validates_destination_and_scope():
    (
        node,
        instance,
        _,
        _,
        _,
        service,
    ) = make_context()

    with pytest.raises(
        TypeError,
        match="destination",
    ):
        service.export_range(
            start=NOW - timedelta(hours=1),
            end=NOW,
            destination="/tmp/export",
        )

    with pytest.raises(
        TypeError,
        match="node_id",
    ):
        service.export_range(
            start=NOW - timedelta(hours=1),
            end=NOW,
            destination=Path("/tmp/export"),
            node_id="streaming-core",
        )

    with pytest.raises(
        TypeError,
        match="instance_id",
    ):
        service.export_range(
            start=NOW - timedelta(hours=1),
            end=NOW,
            destination=Path("/tmp/export"),
            node_id=node.node_id,
            instance_id="streaming-primary",
        )

    assert isinstance(
        instance.instance_id,
        NodeInstanceId,
    )


def test_service_rejects_invalid_repositories():
    events = InMemoryEventHistoryRepository()
    alarms = InMemoryAlarmHistoryRepository()
    exporter = CapturingCsvExportRepository()

    with pytest.raises(TypeError):
        HistoryCsvExportService(
            event_repository=object(),
            alarm_repository=alarms,
            export_repository=exporter,
        )

    with pytest.raises(TypeError):
        HistoryCsvExportService(
            event_repository=events,
            alarm_repository=object(),
            export_repository=exporter,
        )

    with pytest.raises(TypeError):
        HistoryCsvExportService(
            event_repository=events,
            alarm_repository=alarms,
            export_repository=object(),
        )


def test_export_range_passes_same_window_and_scope_to_both_repositories(
    monkeypatch,
) -> None:
    (
        node,
        instance,
        events,
        alarms,
        _,
        service,
    ) = make_context()

    start = NOW - timedelta(hours=6)
    end = NOW - timedelta(hours=1)

    event_calls = []
    alarm_calls = []

    original_event_query = (
        events.list_between
    )

    original_alarm_query = (
        alarms.list_transitions_between
    )

    def capture_events(
        query_start,
        query_end,
        *,
        node_id=None,
        instance_id=None,
    ):
        event_calls.append(
            (
                query_start,
                query_end,
                node_id,
                instance_id,
            )
        )

        return original_event_query(
            query_start,
            query_end,
            node_id=node_id,
            instance_id=instance_id,
        )

    def capture_alarms(
        query_start,
        query_end,
        *,
        node_id=None,
        instance_id=None,
    ):
        alarm_calls.append(
            (
                query_start,
                query_end,
                node_id,
                instance_id,
            )
        )

        return original_alarm_query(
            query_start,
            query_end,
            node_id=node_id,
            instance_id=instance_id,
        )

    monkeypatch.setattr(
        events,
        "list_between",
        capture_events,
    )

    monkeypatch.setattr(
        alarms,
        "list_transitions_between",
        capture_alarms,
    )

    service.export_range(
        start=start,
        end=end,
        destination=Path("/tmp/export"),
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    expected = (
        start,
        end,
        node.node_id,
        instance.instance_id,
    )

    assert event_calls == [
        expected
    ]

    assert alarm_calls == [
        expected
    ]
