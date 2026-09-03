from datetime import datetime, timezone

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
from app.noc.history.alarm_transition import (
    AlarmTransition,
    AlarmTransitionType,
)
from app.noc.history.event_history_record import (
    EventHistoryRecord,
)
from app.noc.history.historical_range_repository import (
    HistoricalRangeRepository,
)
from app.noc.history.sqlite_alarm_repository import (
    SQLiteAlarmHistoryRepository,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)
from app.noc.history.sqlite_event_repository import (
    SQLiteEventHistoryRepository,
)
from app.noc.history.sqlite_historical_range_repository import (
    SQLiteHistoricalRangeRepository,
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

OTHER_INSTANCE = NodeInstanceId(
    "instance-002"
)


def make_database(tmp_path) -> SQLiteHistoryDatabase:
    return SQLiteHistoryDatabase(
        tmp_path / "history.sqlite3"
    )


def append_event(
    database: SQLiteHistoryDatabase,
    *,
    event_id: str,
    timestamp: datetime,
    instance_id: NodeInstanceId = INSTANCE,
) -> None:
    repository = SQLiteEventHistoryRepository(
        database
    )

    event = EventRecord(
        event_id=event_id,
        event_type="TEST_EVENT",
        severity=EventSeverity.INFO,
        timestamp=timestamp,
        source=instance_id,
        title="Test event",
        description="Historical range test event",
    )

    repository.append(
        EventHistoryRecord(
            event=event,
            node_id=NODE,
            instance_id=instance_id,
            recorded_at=timestamp,
        )
    )


def append_transition(
    database: SQLiteHistoryDatabase,
    *,
    alarm_id: str,
    transition_id: str,
    timestamp: datetime,
    instance_id: NodeInstanceId = INSTANCE,
) -> None:
    repository = SQLiteAlarmHistoryRepository(
        database
    )

    alarm = AlarmRecord(
        alarm_id=alarm_id,
        alarm_type="TEST_ALARM",
        severity=AlarmSeverity.WARNING,
        state=AlarmState.ACTIVE,
        timestamp=timestamp,
        source=instance_id,
        title="Test alarm",
        description="Historical range test alarm",
    )

    transition = AlarmTransition(
        transition_id=transition_id,
        alarm_id=alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=timestamp,
        source=instance_id,
        state=AlarmState.ACTIVE,
    )

    repository.record_lifecycle(
        node_id=NODE,
        instance_id=instance_id,
        alarm=alarm,
        transition=transition,
    )



def test_repository_satisfies_protocol(
    tmp_path,
) -> None:
    database = make_database(tmp_path)

    repository = SQLiteHistoricalRangeRepository(
        database
    )

    assert isinstance(
        repository,
        HistoricalRangeRepository,
    )

def test_empty_history_returns_none(
    tmp_path,
) -> None:
    database = make_database(tmp_path)

    repository = SQLiteHistoricalRangeRepository(
        database
    )

    assert repository.first_historical_timestamp(
        node_id=NODE,
        instance_id=INSTANCE,
    ) is None


def test_event_can_define_first_historical_timestamp(
    tmp_path,
) -> None:
    database = make_database(tmp_path)

    event_time = datetime(
        2026,
        9,
        2,
        8,
        0,
        tzinfo=timezone.utc,
    )

    transition_time = datetime(
        2026,
        9,
        2,
        9,
        0,
        tzinfo=timezone.utc,
    )

    append_event(
        database,
        event_id="event-001",
        timestamp=event_time,
    )

    append_transition(
        database,
        alarm_id="alarm-001",
        transition_id="transition-001",
        timestamp=transition_time,
    )

    repository = SQLiteHistoricalRangeRepository(
        database
    )

    assert repository.first_historical_timestamp(
        node_id=NODE,
        instance_id=INSTANCE,
    ) == event_time


def test_alarm_transition_can_define_first_historical_timestamp(
    tmp_path,
) -> None:
    database = make_database(tmp_path)

    transition_time = datetime(
        2026,
        9,
        2,
        7,
        0,
        tzinfo=timezone.utc,
    )

    event_time = datetime(
        2026,
        9,
        2,
        8,
        0,
        tzinfo=timezone.utc,
    )

    append_transition(
        database,
        alarm_id="alarm-001",
        transition_id="transition-001",
        timestamp=transition_time,
    )

    append_event(
        database,
        event_id="event-001",
        timestamp=event_time,
    )

    repository = SQLiteHistoricalRangeRepository(
        database
    )

    assert repository.first_historical_timestamp(
        node_id=NODE,
        instance_id=INSTANCE,
    ) == transition_time


def test_other_instance_is_ignored(
    tmp_path,
) -> None:
    database = make_database(tmp_path)

    other_time = datetime(
        2026,
        9,
        1,
        6,
        0,
        tzinfo=timezone.utc,
    )

    target_time = datetime(
        2026,
        9,
        2,
        8,
        0,
        tzinfo=timezone.utc,
    )

    append_event(
        database,
        event_id="event-other",
        timestamp=other_time,
        instance_id=OTHER_INSTANCE,
    )

    append_event(
        database,
        event_id="event-target",
        timestamp=target_time,
        instance_id=INSTANCE,
    )

    repository = SQLiteHistoricalRangeRepository(
        database
    )

    assert repository.first_historical_timestamp(
        node_id=NODE,
        instance_id=INSTANCE,
    ) == target_time
