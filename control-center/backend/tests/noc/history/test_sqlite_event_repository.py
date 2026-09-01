from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.event_history_record import (
    EventHistoryRecord,
)
from app.noc.history.repository import (
    EventHistoryRepository,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)
from app.noc.history.sqlite_event_repository import (
    SQLiteEventHistoryRepository,
)


T0 = datetime(
    2026,
    9,
    1,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)

T1 = datetime(
    2026,
    9,
    1,
    12,
    1,
    0,
    tzinfo=timezone.utc,
)

T2 = datetime(
    2026,
    9,
    1,
    12,
    2,
    0,
    tzinfo=timezone.utc,
)

T3 = datetime(
    2026,
    9,
    1,
    12,
    3,
    0,
    tzinfo=timezone.utc,
)

INSTANCE = NodeInstanceId(
    "instance-001"
)

NODE = NodeId(
    id="node-001",
    name="node-001",
    display_name="Node 001",
    created_at=T0,
)


def make_record(
    event_id: str,
    timestamp: datetime,
) -> EventHistoryRecord:
    event = EventRecord(
        event_id=event_id,
        event_type="SESSION_CONNECTED",
        severity=EventSeverity.INFO,
        timestamp=timestamp,
        source=INSTANCE,
        title="Session connected",
        description="SRT reader connected",
        correlation_id="corr-001",
        attributes={
            "path": "ejtv",
            "protocol": "SRT",
            "role": "READER",
        },
    )

    return EventHistoryRecord(
        event=event,
        node_id=NODE,
        instance_id=INSTANCE,
        recorded_at=timestamp,
    )


def make_repository(
    tmp_path,
) -> SQLiteEventHistoryRepository:
    database = SQLiteHistoryDatabase(
        tmp_path / "history.sqlite3"
    )

    return SQLiteEventHistoryRepository(
        database
    )


def test_repository_satisfies_protocol(
    tmp_path,
) -> None:
    repository = make_repository(
        tmp_path
    )

    assert isinstance(
        repository,
        EventHistoryRepository,
    )


def test_append_and_get_round_trip(
    tmp_path,
) -> None:
    repository = make_repository(
        tmp_path
    )

    original = make_record(
        "event-001",
        T1,
    )

    repository.append(original)

    loaded = repository.get(
        "event-001"
    )

    assert loaded is not None

    assert loaded.event.event_id == (
        original.event.event_id
    )

    assert loaded.event.event_type == (
        original.event.event_type
    )

    assert loaded.event.severity == (
        original.event.severity
    )

    assert loaded.event.timestamp == (
        original.event.timestamp
    )

    assert loaded.event.source == (
        original.event.source
    )

    assert loaded.event.title == (
        original.event.title
    )

    assert loaded.event.description == (
        original.event.description
    )

    assert loaded.event.correlation_id == (
        original.event.correlation_id
    )

    assert dict(
        loaded.event.attributes
    ) == dict(
        original.event.attributes
    )

    assert loaded.instance_id == (
        original.instance_id
    )

    assert loaded.recorded_at == (
        original.recorded_at
    )

    assert loaded.node_id == (
        original.node_id
    )


def test_event_survives_repository_recreation(
    tmp_path,
) -> None:
    path = (
        tmp_path
        / "history.sqlite3"
    )

    repository = SQLiteEventHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    repository.append(
        make_record(
            "event-001",
            T1,
        )
    )

    del repository

    reopened = SQLiteEventHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    loaded = reopened.get(
        "event-001"
    )

    assert loaded is not None
    assert loaded.event_id == "event-001"


def test_duplicate_event_id_is_rejected(
    tmp_path,
) -> None:
    repository = make_repository(
        tmp_path
    )

    record = make_record(
        "event-001",
        T1,
    )

    repository.append(record)

    with pytest.raises(ValueError):
        repository.append(record)


def test_missing_event_returns_none(
    tmp_path,
) -> None:
    repository = make_repository(
        tmp_path
    )

    assert repository.get(
        "missing-event"
    ) is None


def test_list_between_is_ordered_and_bounded(
    tmp_path,
) -> None:
    repository = make_repository(
        tmp_path
    )

    repository.append(
        make_record(
            "event-003",
            T3,
        )
    )

    repository.append(
        make_record(
            "event-001",
            T1,
        )
    )

    repository.append(
        make_record(
            "event-002",
            T2,
        )
    )

    records = repository.list_between(
        T1,
        T3,
    )

    assert [
        record.event_id
        for record in records
    ] == [
        "event-001",
        "event-002",
    ]


def test_list_between_filters_instance(
    tmp_path,
) -> None:
    repository = make_repository(
        tmp_path
    )

    repository.append(
        make_record(
            "event-001",
            T1,
        )
    )

    records = repository.list_between(
        T0,
        T2,
        instance_id=NodeInstanceId(
            "other-instance"
        ),
    )

    assert records == ()


def test_invalid_window_is_rejected(
    tmp_path,
) -> None:
    repository = make_repository(
        tmp_path
    )

    with pytest.raises(ValueError):
        repository.list_between(
            T2,
            T1,
        )



def test_list_between_rejects_non_utc_window(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    costa_rica = timezone(
        timedelta(hours=-6)
    )

    start = datetime(
        2026,
        9,
        1,
        6,
        0,
        0,
        tzinfo=costa_rica,
    )

    end = datetime(
        2026,
        9,
        1,
        7,
        0,
        0,
        tzinfo=costa_rica,
    )

    with pytest.raises(ValueError):
        repository.list_between(
            start,
            end,
        )
