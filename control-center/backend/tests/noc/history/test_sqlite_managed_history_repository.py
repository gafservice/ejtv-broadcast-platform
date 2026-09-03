from datetime import date, datetime, timezone

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.managed_history_repository import (
    ManagedHistoryRepository,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)
from app.noc.history.sqlite_managed_history_repository import (
    SQLiteManagedHistoryRepository,
)


NODE = NodeId(
    id="node-001",
    name="node-001",
    display_name="Node 001",
    created_at=datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    ),
)

INSTANCE = NodeInstanceId(
    "instance-001"
)

T0 = datetime(
    2026,
    9,
    2,
    8,
    0,
    tzinfo=timezone.utc,
)


def make_repository(
    tmp_path,
) -> SQLiteManagedHistoryRepository:
    return SQLiteManagedHistoryRepository(
        SQLiteHistoryDatabase(
            tmp_path / "history.sqlite3"
        )
    )


def test_repository_satisfies_protocol(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    assert isinstance(
        repository,
        ManagedHistoryRepository,
    )


def test_empty_scope_returns_none(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    assert repository.get_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
    ) is None


def test_ensure_creates_anchor(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    managed_day = date(
        2026,
        9,
        2,
    )

    result = repository.ensure_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
        day=managed_day,
        created_at=T0,
    )

    assert result == managed_day

    assert repository.get_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
    ) == managed_day


def test_ensure_does_not_move_existing_anchor_forward(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    first_day = date(
        2026,
        9,
        2,
    )

    repository.ensure_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
        day=first_day,
        created_at=T0,
    )

    result = repository.ensure_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
        day=date(
            2026,
            9,
            10,
        ),
        created_at=datetime(
            2026,
            9,
            10,
            tzinfo=timezone.utc,
        ),
    )

    assert result == first_day

    assert repository.get_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
    ) == first_day


def test_anchor_survives_repository_recreation(
    tmp_path,
) -> None:
    path = tmp_path / "history.sqlite3"

    repository = SQLiteManagedHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    managed_day = date(
        2026,
        9,
        2,
    )

    repository.ensure_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
        day=managed_day,
        created_at=T0,
    )

    del repository

    reopened = SQLiteManagedHistoryRepository(
        SQLiteHistoryDatabase(path)
    )

    assert reopened.get_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
    ) == managed_day


def test_managed_history_is_isolated_by_instance(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    other_instance = NodeInstanceId(
        "instance-002"
    )

    first_day = date(
        2026,
        9,
        2,
    )

    other_day = date(
        2026,
        9,
        5,
    )

    repository.ensure_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
        day=first_day,
        created_at=T0,
    )

    repository.ensure_managed_since_day(
        node_id=NODE,
        instance_id=other_instance,
        day=other_day,
        created_at=datetime(
            2026,
            9,
            5,
            tzinfo=timezone.utc,
        ),
    )

    assert repository.get_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
    ) == first_day

    assert repository.get_managed_since_day(
        node_id=NODE,
        instance_id=other_instance,
    ) == other_day


def test_ensure_never_moves_existing_anchor_backward(
    tmp_path,
) -> None:
    repository = make_repository(tmp_path)

    original_day = date(
        2026,
        9,
        5,
    )

    repository.ensure_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
        day=original_day,
        created_at=datetime(
            2026,
            9,
            5,
            tzinfo=timezone.utc,
        ),
    )

    result = repository.ensure_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
        day=date(
            2026,
            9,
            2,
        ),
        created_at=T0,
    )

    assert result == original_day

    assert repository.get_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
    ) == original_day


def test_anchor_survives_deletion_of_old_historical_rows(
    tmp_path,
) -> None:
    path = tmp_path / "history.sqlite3"
    database = SQLiteHistoryDatabase(path)

    repository = SQLiteManagedHistoryRepository(
        database
    )

    managed_day = date(
        2026,
        9,
        2,
    )

    repository.ensure_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
        day=managed_day,
        created_at=T0,
    )

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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "old-event",
                NODE.id,
                NODE.name,
                NODE.display_name,
                NODE.created_at.isoformat(),
                INSTANCE.value,
                "TEST_EVENT",
                "INFO",
                "2026-09-02T08:00:00+00:00",
                "2026-09-02T08:00:00+00:00",
                INSTANCE.value,
                "Old event",
                "Retention simulation",
                None,
                None,
            ),
        )

    with database.connect() as connection:
        connection.execute(
            """
            DELETE FROM events
            WHERE event_id = ?
            """,
            ("old-event",),
        )

    assert repository.get_managed_since_day(
        node_id=NODE,
        instance_id=INSTANCE,
    ) == managed_day
