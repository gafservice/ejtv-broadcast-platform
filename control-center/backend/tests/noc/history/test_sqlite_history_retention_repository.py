from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.history_retention_repository import (
    HistoryRetentionRepository,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)
from app.noc.history.sqlite_history_retention_repository import (
    SQLiteHistoryRetentionRepository,
)
from app.noc.history.sqlite_managed_history_repository import (
    SQLiteManagedHistoryRepository,
)


UTC = timezone.utc

NODE = NodeId(
    id="streaming-core",
    name="streaming-core",
    display_name="Streaming Core",
    created_at=datetime(2026, 9, 1, tzinfo=UTC),
)

OTHER_NODE = NodeId(
    id="other-node",
    name="other-node",
    display_name="Other Node",
    created_at=datetime(2026, 9, 1, tzinfo=UTC),
)

INSTANCE = NodeInstanceId(
    "streaming-primary"
)

OTHER_INSTANCE = NodeInstanceId(
    "streaming-secondary"
)

CUTOFF = datetime(
    2026,
    9,
    10,
    tzinfo=UTC,
)


def _iso(value: datetime) -> str:
    return value.isoformat(
        timespec="microseconds"
    )


def _insert_event(
    database: SQLiteHistoryDatabase,
    *,
    event_id: str,
    timestamp: datetime,
    node_id: NodeId = NODE,
    instance_id: NodeInstanceId = INSTANCE,
) -> None:
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO events (
                event_id,
                node_id,
                node_name,
                node_display_name,
                node_created_at,
                instance_id,
                event_type,
                severity,
                event_timestamp,
                recorded_at,
                source,
                title,
                description,
                correlation_id,
                attributes_json
            )
            VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?
            )
            """,
            (
                event_id,
                node_id.id,
                node_id.name,
                node_id.display_name,
                _iso(node_id.created_at),
                instance_id.value,
                "TEST_EVENT",
                "INFO",
                _iso(timestamp),
                _iso(timestamp),
                instance_id.value,
                "Test event",
                "Retention test event",
                None,
                None,
            ),
        )


def _insert_alarm(
    database: SQLiteHistoryDatabase,
    *,
    alarm_id: str,
    state: str,
    opened_at: datetime,
    node_id: NodeId = NODE,
    instance_id: NodeInstanceId = INSTANCE,
) -> None:
    acknowledged = int(
        state == "ACKNOWLEDGED"
    )

    acknowledged_at = (
        _iso(opened_at + timedelta(minutes=1))
        if acknowledged
        else None
    )

    resolved_at = (
        _iso(opened_at + timedelta(minutes=2))
        if state == "RESOLVED"
        else None
    )

    closed_at = (
        _iso(opened_at + timedelta(minutes=3))
        if state == "CLOSED"
        else None
    )

    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO alarms (
                alarm_id,
                node_id,
                node_name,
                node_display_name,
                node_created_at,
                instance_id,
                alarm_type,
                severity,
                state,
                opened_at,
                source,
                title,
                description,
                acknowledged,
                acknowledged_by,
                acknowledged_at,
                resolved_at,
                closed_at,
                correlation_id,
                attributes_json
            )
            VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?
            )
            """,
            (
                alarm_id,
                node_id.id,
                node_id.name,
                node_id.display_name,
                _iso(node_id.created_at),
                instance_id.value,
                "TEST_ALARM",
                "MAJOR",
                state,
                _iso(opened_at),
                instance_id.value,
                "Test alarm",
                "Retention test alarm",
                acknowledged,
                (
                    "operator"
                    if acknowledged
                    else None
                ),
                acknowledged_at,
                resolved_at,
                closed_at,
                None,
                "{}",
            ),
        )


def _insert_transition(
    database: SQLiteHistoryDatabase,
    *,
    transition_id: str,
    alarm_id: str,
    timestamp: datetime,
    state: str,
    transition_type: str,
    instance_id: NodeInstanceId = INSTANCE,
) -> None:
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO alarm_transitions (
                transition_id,
                alarm_id,
                transition_type,
                transition_timestamp,
                source,
                state,
                actor,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transition_id,
                alarm_id,
                transition_type,
                _iso(timestamp),
                instance_id.value,
                state,
                None,
                "{}",
            ),
        )


def _row_exists(
    database: SQLiteHistoryDatabase,
    table: str,
    id_column: str,
    value: str,
) -> bool:
    with database.connect() as connection:
        row = connection.execute(
            f"""
            SELECT 1
            FROM {table}
            WHERE {id_column} = ?
            """,
            (value,),
        ).fetchone()

    return row is not None


def _repository(
    tmp_path,
) -> tuple[
    SQLiteHistoryDatabase,
    SQLiteHistoryRetentionRepository,
]:
    database = SQLiteHistoryDatabase(
        tmp_path / "history.sqlite3"
    )

    database.initialize()

    return (
        database,
        SQLiteHistoryRetentionRepository(
            database
        ),
    )


def test_repository_satisfies_retention_protocol(
    tmp_path,
) -> None:
    _, repository = _repository(tmp_path)

    assert isinstance(
        repository,
        HistoryRetentionRepository,
    )


def test_events_are_pruned_strictly_before_cutoff(
    tmp_path,
) -> None:
    database, repository = _repository(tmp_path)

    _insert_event(
        database,
        event_id="before",
        timestamp=CUTOFF - timedelta(microseconds=1),
    )
    _insert_event(
        database,
        event_id="at-cutoff",
        timestamp=CUTOFF,
    )
    _insert_event(
        database,
        event_id="after",
        timestamp=CUTOFF + timedelta(microseconds=1),
    )

    result = repository.prune_before(
        node_id=NODE,
        instance_id=INSTANCE,
        cutoff=CUTOFF,
    )

    assert result.events_deleted == 1
    assert not _row_exists(
        database,
        "events",
        "event_id",
        "before",
    )
    assert _row_exists(
        database,
        "events",
        "event_id",
        "at-cutoff",
    )
    assert _row_exists(
        database,
        "events",
        "event_id",
        "after",
    )


def test_retention_is_isolated_by_node_and_instance(
    tmp_path,
) -> None:
    database, repository = _repository(tmp_path)

    old = CUTOFF - timedelta(days=1)

    _insert_event(
        database,
        event_id="target",
        timestamp=old,
    )
    _insert_event(
        database,
        event_id="other-instance",
        timestamp=old,
        instance_id=OTHER_INSTANCE,
    )
    _insert_event(
        database,
        event_id="other-node",
        timestamp=old,
        node_id=OTHER_NODE,
    )

    repository.prune_before(
        node_id=NODE,
        instance_id=INSTANCE,
        cutoff=CUTOFF,
    )

    assert not _row_exists(
        database,
        "events",
        "event_id",
        "target",
    )
    assert _row_exists(
        database,
        "events",
        "event_id",
        "other-instance",
    )
    assert _row_exists(
        database,
        "events",
        "event_id",
        "other-node",
    )


@pytest.mark.parametrize(
    "state",
    (
        "ACTIVE",
        "ACKNOWLEDGED",
    ),
)
def test_non_terminal_alarm_keeps_complete_lifecycle(
    tmp_path,
    state: str,
) -> None:
    database, repository = _repository(tmp_path)

    opened = CUTOFF - timedelta(days=5)

    alarm_id = f"alarm-{state.lower()}"

    _insert_alarm(
        database,
        alarm_id=alarm_id,
        state=state,
        opened_at=opened,
    )
    _insert_transition(
        database,
        transition_id=f"{alarm_id}-opened",
        alarm_id=alarm_id,
        timestamp=opened,
        state="ACTIVE",
        transition_type="OPENED",
    )

    repository.prune_before(
        node_id=NODE,
        instance_id=INSTANCE,
        cutoff=CUTOFF,
    )

    assert _row_exists(
        database,
        "alarms",
        "alarm_id",
        alarm_id,
    )
    assert _row_exists(
        database,
        "alarm_transitions",
        "transition_id",
        f"{alarm_id}-opened",
    )


@pytest.mark.parametrize(
    "state, transition_type",
    (
        ("RESOLVED", "RESOLVED"),
        ("CLOSED", "CLOSED"),
        ("INVALIDATED", "INVALIDATED"),
    ),
)
def test_terminal_alarm_with_complete_old_lifecycle_is_deleted(
    tmp_path,
    state: str,
    transition_type: str,
) -> None:
    database, repository = _repository(tmp_path)

    opened = CUTOFF - timedelta(days=5)
    terminal = CUTOFF - timedelta(days=4)

    alarm_id = f"terminal-{state.lower()}"

    _insert_alarm(
        database,
        alarm_id=alarm_id,
        state=state,
        opened_at=opened,
    )
    _insert_transition(
        database,
        transition_id=f"{alarm_id}-opened",
        alarm_id=alarm_id,
        timestamp=opened,
        state="ACTIVE",
        transition_type="OPENED",
    )
    _insert_transition(
        database,
        transition_id=f"{alarm_id}-terminal",
        alarm_id=alarm_id,
        timestamp=terminal,
        state=state,
        transition_type=transition_type,
    )

    result = repository.prune_before(
        node_id=NODE,
        instance_id=INSTANCE,
        cutoff=CUTOFF,
    )

    assert result.alarms_deleted == 1
    assert result.alarm_transitions_deleted == 2

    assert not _row_exists(
        database,
        "alarms",
        "alarm_id",
        alarm_id,
    )
    assert not _row_exists(
        database,
        "alarm_transitions",
        "transition_id",
        f"{alarm_id}-opened",
    )
    assert not _row_exists(
        database,
        "alarm_transitions",
        "transition_id",
        f"{alarm_id}-terminal",
    )


def test_terminal_alarm_with_transition_at_cutoff_is_kept_complete(
    tmp_path,
) -> None:
    database, repository = _repository(tmp_path)

    opened = CUTOFF - timedelta(days=5)

    _insert_alarm(
        database,
        alarm_id="crosses-cutoff",
        state="RESOLVED",
        opened_at=opened,
    )
    _insert_transition(
        database,
        transition_id="crosses-cutoff-opened",
        alarm_id="crosses-cutoff",
        timestamp=opened,
        state="ACTIVE",
        transition_type="OPENED",
    )
    _insert_transition(
        database,
        transition_id="crosses-cutoff-resolved",
        alarm_id="crosses-cutoff",
        timestamp=CUTOFF,
        state="RESOLVED",
        transition_type="RESOLVED",
    )

    result = repository.prune_before(
        node_id=NODE,
        instance_id=INSTANCE,
        cutoff=CUTOFF,
    )

    assert result.alarms_deleted == 0
    assert result.alarm_transitions_deleted == 0

    assert _row_exists(
        database,
        "alarms",
        "alarm_id",
        "crosses-cutoff",
    )
    assert _row_exists(
        database,
        "alarm_transitions",
        "transition_id",
        "crosses-cutoff-opened",
    )
    assert _row_exists(
        database,
        "alarm_transitions",
        "transition_id",
        "crosses-cutoff-resolved",
    )


def test_terminal_alarm_without_transitions_is_kept_fail_safe(
    tmp_path,
) -> None:
    database, repository = _repository(tmp_path)

    _insert_alarm(
        database,
        alarm_id="orphan-terminal",
        state="RESOLVED",
        opened_at=CUTOFF - timedelta(days=5),
    )

    result = repository.prune_before(
        node_id=NODE,
        instance_id=INSTANCE,
        cutoff=CUTOFF,
    )

    assert result.alarms_deleted == 0
    assert result.alarm_transitions_deleted == 0

    assert _row_exists(
        database,
        "alarms",
        "alarm_id",
        "orphan-terminal",
    )


def test_managed_history_anchor_is_not_modified(
    tmp_path,
) -> None:
    database, repository = _repository(tmp_path)

    managed_history = SQLiteManagedHistoryRepository(
        database
    )

    managed_day = datetime(
        2026,
        9,
        1,
        tzinfo=UTC,
    ).date()

    managed_history.ensure_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
        day=managed_day,
        created_at=datetime(
            2026,
            9,
            1,
            12,
            tzinfo=UTC,
        ),
    )

    _insert_event(
        database,
        event_id="old-event",
        timestamp=CUTOFF - timedelta(days=1),
    )

    repository.prune_before(
        node_id=NODE,
        instance_id=INSTANCE,
        cutoff=CUTOFF,
    )

    assert (
        managed_history.get_managed_since_day(
            node_id=NODE,
            instance_id=INSTANCE,
        )
        == managed_day
    )


def test_prune_is_atomic_if_parent_alarm_delete_fails(
    tmp_path,
) -> None:
    database, repository = _repository(tmp_path)

    opened = CUTOFF - timedelta(days=5)

    _insert_alarm(
        database,
        alarm_id="atomic-alarm",
        state="RESOLVED",
        opened_at=opened,
    )
    _insert_transition(
        database,
        transition_id="atomic-opened",
        alarm_id="atomic-alarm",
        timestamp=opened,
        state="ACTIVE",
        transition_type="OPENED",
    )
    _insert_transition(
        database,
        transition_id="atomic-resolved",
        alarm_id="atomic-alarm",
        timestamp=opened + timedelta(hours=1),
        state="RESOLVED",
        transition_type="RESOLVED",
    )

    with database.connect() as connection:
        connection.execute(
            """
            CREATE TRIGGER fail_alarm_delete
            BEFORE DELETE ON alarms
            WHEN OLD.alarm_id = 'atomic-alarm'
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'forced retention failure'
                );
            END;
            """
        )

    with pytest.raises(
        Exception,
        match="forced retention failure",
    ):
        repository.prune_before(
            node_id=NODE,
            instance_id=INSTANCE,
            cutoff=CUTOFF,
        )

    assert _row_exists(
        database,
        "alarms",
        "alarm_id",
        "atomic-alarm",
    )
    assert _row_exists(
        database,
        "alarm_transitions",
        "transition_id",
        "atomic-opened",
    )
    assert _row_exists(
        database,
        "alarm_transitions",
        "transition_id",
        "atomic-resolved",
    )


def test_cutoff_must_be_timezone_aware(
    tmp_path,
) -> None:
    _, repository = _repository(tmp_path)

    with pytest.raises(
        ValueError,
        match="cutoff must be timezone-aware",
    ):
        repository.prune_before(
            node_id=NODE,
            instance_id=INSTANCE,
            cutoff=datetime(2026, 9, 10),
        )


def test_cutoff_must_be_expressed_in_utc(
    tmp_path,
) -> None:
    _, repository = _repository(tmp_path)

    with pytest.raises(
        ValueError,
        match="cutoff must be expressed in UTC",
    ):
        repository.prune_before(
            node_id=NODE,
            instance_id=INSTANCE,
            cutoff=datetime(
                2026,
                9,
                10,
                tzinfo=timezone(
                    timedelta(hours=-6)
                ),
            ),
        )
