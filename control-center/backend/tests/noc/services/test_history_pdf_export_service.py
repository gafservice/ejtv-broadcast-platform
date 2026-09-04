"""Tests for durable NOC history PDF export coordination."""

from __future__ import annotations

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
from app.noc.history.event_history_record import (
    EventHistoryRecord,
)
from app.noc.history.memory_repository import (
    InMemoryAlarmHistoryRepository,
    InMemoryEventHistoryRepository,
)
from app.noc.history.pdf_export_repository import (
    PdfExportResult,
)
from app.noc.services.history_pdf_export_service import (
    HistoryPdfExportService,
)


NOW = datetime(
    2026,
    9,
    4,
    18,
    0,
    tzinfo=timezone.utc,
)


class CapturingPdfExportRepository:
    def __init__(self) -> None:
        self.calls = []

    def publish(
        self,
        *,
        destination,
        pdf_document,
    ):
        self.calls.append(
            (
                destination,
                pdf_document,
            )
        )

        return PdfExportResult(
            path=destination,
            report_file=(
                destination
                / "history-report.pdf"
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
    exporter = CapturingPdfExportRepository()

    service = HistoryPdfExportService(
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


def test_export_range_renders_and_publishes_requested_history():
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

    destination = Path(
        "/tmp/pdf-export"
    )

    result = service.export_range(
        start=NOW - timedelta(hours=3),
        end=NOW,
        destination=destination,
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert result.path == destination
    assert result.report_file == (
        destination
        / "history-report.pdf"
    )

    assert len(exporter.calls) == 1

    published_destination, document = (
        exporter.calls[0]
    )

    assert published_destination == destination
    assert document.startswith(
        b"%PDF-"
    )
    assert b"%%EOF" in document[-32:]


def test_export_empty_range_still_publishes_pdf():
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
        destination=Path("/tmp/pdf-export"),
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert len(exporter.calls) == 1

    document = exporter.calls[0][1]

    assert document.startswith(
        b"%PDF-"
    )


def test_export_range_uses_half_open_window(
    monkeypatch,
):
    (
        node,
        instance,
        events,
        alarms,
        _,
        service,
    ) = make_context()

    start = NOW - timedelta(hours=2)
    end = NOW

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
        destination=Path("/tmp/pdf-export"),
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
        destination=Path("/tmp/pdf-export"),
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    document = exporter.calls[0][1]

    assert document.startswith(
        b"%PDF-"
    )


@pytest.mark.parametrize(
    (
        "start",
        "end",
    ),
    (
        (
            NOW,
            NOW,
        ),
        (
            NOW,
            NOW - timedelta(seconds=1),
        ),
    ),
)
def test_export_range_rejects_invalid_window(
    start,
    end,
):
    *_, service = make_context()

    with pytest.raises(
        ValueError,
        match="start must be earlier than end",
    ):
        service.export_range(
            start=start,
            end=end,
            destination=Path("/tmp/pdf-export"),
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
            destination=Path("/tmp/pdf-export"),
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
            destination=Path("/tmp/pdf-export"),
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
            destination="/tmp/pdf-export",
        )

    with pytest.raises(
        TypeError,
        match="node_id",
    ):
        service.export_range(
            start=NOW - timedelta(hours=1),
            end=NOW,
            destination=Path("/tmp/pdf-export"),
            node_id="streaming-core",
        )

    with pytest.raises(
        TypeError,
        match="instance_id",
    ):
        service.export_range(
            start=NOW - timedelta(hours=1),
            end=NOW,
            destination=Path("/tmp/pdf-export"),
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
    exporter = CapturingPdfExportRepository()

    with pytest.raises(TypeError):
        HistoryPdfExportService(
            event_repository=object(),
            alarm_repository=alarms,
            export_repository=exporter,
        )

    with pytest.raises(TypeError):
        HistoryPdfExportService(
            event_repository=events,
            alarm_repository=object(),
            export_repository=exporter,
        )

    with pytest.raises(TypeError):
        HistoryPdfExportService(
            event_repository=events,
            alarm_repository=alarms,
            export_repository=object(),
        )
