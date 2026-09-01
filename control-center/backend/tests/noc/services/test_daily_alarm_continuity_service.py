from datetime import date, datetime, timezone

from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.alarm_transition import (
    AlarmTransitionType,
)
from app.noc.history.memory_repository import (
    InMemoryAlarmHistoryRepository,
)
from app.noc.services.daily_alarm_continuity_service import (
    DailyAlarmContinuityService,
)


NODE_ID = NodeId(
    id="streaming-core",
    name="streaming-core",
    display_name="Streaming Core",
    created_at=datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    ),
)

INSTANCE_ID = NodeInstanceId(
    "streaming-primary"
)

BOUNDARY_DAY = date(2026, 9, 2)


def make_alarm(
    *,
    alarm_id: str,
    state: AlarmState = AlarmState.ACTIVE,
    timestamp: datetime | None = None,
) -> AlarmRecord:
    opened_at = timestamp or datetime(
        2026,
        9,
        1,
        23,
        30,
        tzinfo=timezone.utc,
    )

    acknowledged = (
        state is AlarmState.ACKNOWLEDGED
    )

    acknowledged_at = (
        datetime(
            2026,
            9,
            1,
            23,
            45,
            tzinfo=timezone.utc,
        )
        if acknowledged
        else None
    )

    return AlarmRecord(
        alarm_id=alarm_id,
        alarm_type="DAILY_CONTINUITY_TEST",
        severity=AlarmSeverity.MAJOR,
        state=state,
        timestamp=opened_at,
        source=INSTANCE_ID,
        title="Daily continuity test",
        description="Daily continuity test alarm",
        acknowledged=acknowledged,
        acknowledged_by=(
            "operator"
            if acknowledged
            else None
        ),
        acknowledged_at=acknowledged_at,
    )


def seed_alarm(
    repository,
    alarm,
) -> None:
    repository.save_current(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=alarm,
    )


def test_active_alarm_is_carried_forward() -> None:
    repository = InMemoryAlarmHistoryRepository()

    alarm = make_alarm(
        alarm_id="alarm-active",
    )
    seed_alarm(repository, alarm)

    service = DailyAlarmContinuityService(
        repository
    )

    result = service.carry_forward(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        day=BOUNDARY_DAY,
    )

    assert result.carried_forward_count == 1

    transition = result.carried_forward[0]

    assert transition.alarm_id == alarm.alarm_id
    assert (
        transition.transition_type
        is AlarmTransitionType.CARRIED_FORWARD
    )
    assert transition.timestamp == datetime(
        2026,
        9,
        2,
        0,
        0,
        tzinfo=timezone.utc,
    )
    assert transition.state is AlarmState.ACTIVE

    assert repository.get_current(
        alarm.alarm_id
    ) == alarm


def test_acknowledged_alarm_is_carried_forward() -> None:
    repository = InMemoryAlarmHistoryRepository()

    alarm = make_alarm(
        alarm_id="alarm-acknowledged",
        state=AlarmState.ACKNOWLEDGED,
    )
    seed_alarm(repository, alarm)

    service = DailyAlarmContinuityService(
        repository
    )

    result = service.carry_forward(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        day=BOUNDARY_DAY,
    )

    assert result.carried_forward_count == 1
    assert (
        result.carried_forward[0].state
        is AlarmState.ACKNOWLEDGED
    )


def test_alarm_opened_on_boundary_is_not_carried() -> None:
    repository = InMemoryAlarmHistoryRepository()

    alarm = make_alarm(
        alarm_id="alarm-boundary",
        timestamp=datetime(
            2026,
            9,
            2,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )
    seed_alarm(repository, alarm)

    service = DailyAlarmContinuityService(
        repository
    )

    result = service.carry_forward(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        day=BOUNDARY_DAY,
    )

    assert result.carried_forward_count == 0


def test_exact_retry_is_idempotent() -> None:
    repository = InMemoryAlarmHistoryRepository()

    alarm = make_alarm(
        alarm_id="alarm-retry",
    )
    seed_alarm(repository, alarm)

    service = DailyAlarmContinuityService(
        repository
    )

    first = service.carry_forward(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        day=BOUNDARY_DAY,
    )

    second = service.carry_forward(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        day=BOUNDARY_DAY,
    )

    transitions = repository.list_transitions(
        alarm.alarm_id
    )

    assert first.carried_forward_count == 1
    assert second.carried_forward_count == 1
    assert len(transitions) == 1
    assert (
        transitions[0].transition_id
        == first.carried_forward[0].transition_id
        == second.carried_forward[0].transition_id
    )


def test_alarm_identity_and_open_timestamp_are_preserved() -> None:
    repository = InMemoryAlarmHistoryRepository()

    alarm = make_alarm(
        alarm_id="alarm-identity",
    )
    seed_alarm(repository, alarm)

    original_timestamp = alarm.timestamp

    service = DailyAlarmContinuityService(
        repository
    )

    service.carry_forward(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        day=BOUNDARY_DAY,
    )

    current = repository.get_current(
        alarm.alarm_id
    )

    assert current is not None
    assert current.alarm_id == "alarm-identity"
    assert current.timestamp == original_timestamp


def test_carried_forward_is_written_to_new_day_jsonl(
    tmp_path,
) -> None:
    from app.noc.history.jsonl_evidence_writer import (
        JsonlEvidenceWriter,
    )

    repository = InMemoryAlarmHistoryRepository()

    alarm = make_alarm(
        alarm_id="alarm-jsonl-day2",
    )
    seed_alarm(repository, alarm)

    writer = JsonlEvidenceWriter(
        tmp_path
    )

    service = DailyAlarmContinuityService(
        repository,
        evidence_writer=writer,
    )

    result = service.carry_forward(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        day=BOUNDARY_DAY,
    )

    assert result.carried_forward_count == 1

    path = (
        tmp_path
        / "2026"
        / "09"
        / "02"
        / "alarm_transitions.jsonl"
    )

    assert path.exists()

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    import json

    payload = json.loads(lines[0])

    assert payload["alarm_id"] == alarm.alarm_id
    assert (
        payload["transition_type"]
        == "CARRIED_FORWARD"
    )
    assert (
        payload["timestamp"]
        == "2026-09-02T00:00:00Z"
    )
    assert payload["state"] == "ACTIVE"


def test_carried_forward_jsonl_retry_is_idempotent(
    tmp_path,
) -> None:
    from app.noc.history.jsonl_evidence_writer import (
        JsonlEvidenceWriter,
    )

    repository = InMemoryAlarmHistoryRepository()

    alarm = make_alarm(
        alarm_id="alarm-jsonl-retry",
    )
    seed_alarm(repository, alarm)

    writer = JsonlEvidenceWriter(
        tmp_path
    )

    service = DailyAlarmContinuityService(
        repository,
        evidence_writer=writer,
    )

    service.carry_forward(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        day=BOUNDARY_DAY,
    )

    service.carry_forward(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        day=BOUNDARY_DAY,
    )

    path = (
        tmp_path
        / "2026"
        / "09"
        / "02"
        / "alarm_transitions.jsonl"
    )

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1


def test_alarm_continues_across_multiple_days(
    tmp_path,
) -> None:
    from app.noc.history.jsonl_evidence_writer import (
        JsonlEvidenceWriter,
    )

    repository = InMemoryAlarmHistoryRepository()

    alarm = make_alarm(
        alarm_id="alarm-multiday",
        timestamp=datetime(
            2026,
            9,
            1,
            22,
            15,
            tzinfo=timezone.utc,
        ),
    )
    seed_alarm(repository, alarm)

    writer = JsonlEvidenceWriter(
        tmp_path
    )

    service = DailyAlarmContinuityService(
        repository,
        evidence_writer=writer,
    )

    days = (
        date(2026, 9, 2),
        date(2026, 9, 3),
        date(2026, 9, 4),
    )

    for day in days:
        result = service.carry_forward(
            node_id=NODE_ID,
            instance_id=INSTANCE_ID,
            day=day,
        )

        assert result.carried_forward_count == 1

    transitions = repository.list_transitions(
        alarm.alarm_id
    )

    assert len(transitions) == 3

    assert all(
        transition.alarm_id
        == alarm.alarm_id
        for transition in transitions
    )

    assert all(
        transition.transition_type
        is AlarmTransitionType.CARRIED_FORWARD
        for transition in transitions
    )

    assert tuple(
        transition.timestamp
        for transition in transitions
    ) == (
        datetime(
            2026,
            9,
            2,
            0,
            0,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            9,
            3,
            0,
            0,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            9,
            4,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )

    transition_ids = {
        transition.transition_id
        for transition in transitions
    }

    assert len(transition_ids) == 3

    current = repository.get_current(
        alarm.alarm_id
    )

    assert current == alarm

    for day in ("02", "03", "04"):
        path = (
            tmp_path
            / "2026"
            / "09"
            / day
            / "alarm_transitions.jsonl"
        )

        assert path.exists()

        lines = path.read_text(
            encoding="utf-8"
        ).splitlines()

        assert len(lines) == 1


def test_sqlite_continuity_survives_repository_reopen(
    tmp_path,
) -> None:
    from app.noc.history.jsonl_evidence_writer import (
        JsonlEvidenceWriter,
    )
    from app.noc.history.sqlite_alarm_repository import (
        SQLiteAlarmHistoryRepository,
    )
    from app.noc.history.sqlite_database import (
        SQLiteHistoryDatabase,
    )

    db_path = tmp_path / "history.db"
    evidence_path = tmp_path / "evidence"

    database = SQLiteHistoryDatabase(
        db_path
    )

    repository = SQLiteAlarmHistoryRepository(
        database
    )

    alarm = make_alarm(
        alarm_id="alarm-sqlite-reopen",
        timestamp=datetime(
            2026,
            9,
            1,
            22,
            0,
            tzinfo=timezone.utc,
        ),
    )

    repository.save_current(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=alarm,
    )

    writer = JsonlEvidenceWriter(
        evidence_path
    )

    first_service = DailyAlarmContinuityService(
        repository,
        evidence_writer=writer,
    )

    first = first_service.carry_forward(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        day=date(2026, 9, 2),
    )

    assert first.carried_forward_count == 1

    del first_service
    del repository
    del database

    reopened_database = SQLiteHistoryDatabase(
        db_path
    )

    reopened_repository = (
        SQLiteAlarmHistoryRepository(
            reopened_database
        )
    )

    reopened_writer = JsonlEvidenceWriter(
        evidence_path
    )

    second_service = DailyAlarmContinuityService(
        reopened_repository,
        evidence_writer=reopened_writer,
    )

    second = second_service.carry_forward(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        day=date(2026, 9, 3),
    )

    assert second.carried_forward_count == 1

    current = reopened_repository.get_current(
        alarm.alarm_id
    )

    assert current == alarm

    transitions = (
        reopened_repository.list_transitions(
            alarm.alarm_id
        )
    )

    assert len(transitions) == 2

    assert tuple(
        transition.timestamp
        for transition in transitions
    ) == (
        datetime(
            2026,
            9,
            2,
            0,
            0,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            9,
            3,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert all(
        transition.transition_type
        is AlarmTransitionType.CARRIED_FORWARD
        for transition in transitions
    )

    for day in ("02", "03"):
        path = (
            evidence_path
            / "2026"
            / "09"
            / day
            / "alarm_transitions.jsonl"
        )

        assert path.exists()
        assert len(
            path.read_text(
                encoding="utf-8"
            ).splitlines()
        ) == 1


def test_catch_up_reconstructs_missing_daily_boundaries(
    tmp_path,
) -> None:
    from app.noc.history.jsonl_evidence_writer import (
        JsonlEvidenceWriter,
    )

    repository = InMemoryAlarmHistoryRepository()

    alarm = make_alarm(
        alarm_id="alarm-catch-up",
        timestamp=datetime(
            2026,
            9,
            1,
            22,
            0,
            tzinfo=timezone.utc,
        ),
    )
    seed_alarm(repository, alarm)

    writer = JsonlEvidenceWriter(tmp_path)

    service = DailyAlarmContinuityService(
        repository,
        evidence_writer=writer,
    )

    result = service.catch_up(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        through=datetime(
            2026,
            9,
            4,
            8,
            30,
            tzinfo=timezone.utc,
        ),
    )

    assert result.carried_forward_count == 3

    transitions = repository.list_transitions(
        alarm.alarm_id
    )

    assert tuple(
        transition.timestamp
        for transition in transitions
    ) == (
        datetime(
            2026, 9, 2, 0, 0,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026, 9, 3, 0, 0,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026, 9, 4, 0, 0,
            tzinfo=timezone.utc,
        ),
    )

    for day in ("02", "03", "04"):
        path = (
            tmp_path
            / "2026"
            / "09"
            / day
            / "alarm_transitions.jsonl"
        )

        assert path.exists()
        assert len(
            path.read_text(
                encoding="utf-8"
            ).splitlines()
        ) == 1


def test_catch_up_exact_retry_is_idempotent(
    tmp_path,
) -> None:
    from app.noc.history.jsonl_evidence_writer import (
        JsonlEvidenceWriter,
    )

    repository = InMemoryAlarmHistoryRepository()

    alarm = make_alarm(
        alarm_id="alarm-catch-up-retry",
        timestamp=datetime(
            2026,
            9,
            1,
            22,
            0,
            tzinfo=timezone.utc,
        ),
    )
    seed_alarm(repository, alarm)

    writer = JsonlEvidenceWriter(tmp_path)

    service = DailyAlarmContinuityService(
        repository,
        evidence_writer=writer,
    )

    through = datetime(
        2026,
        9,
        4,
        8,
        30,
        tzinfo=timezone.utc,
    )

    first = service.catch_up(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        through=through,
    )

    second = service.catch_up(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        through=through,
    )

    transitions = repository.list_transitions(
        alarm.alarm_id
    )

    assert first.carried_forward_count == 3
    assert second.carried_forward_count == 3
    assert len(transitions) == 3

    assert len(
        {
            transition.transition_id
            for transition in transitions
        }
    ) == 3


def test_historical_boundary_before_resolution_is_carried_forward(
    tmp_path,
) -> None:
    from dataclasses import replace

    from app.noc.history.alarm_transition import (
        AlarmTransition,
        make_alarm_transition_id,
    )
    from app.noc.history.jsonl_evidence_writer import (
        JsonlEvidenceWriter,
    )

    repository = InMemoryAlarmHistoryRepository()

    opened = make_alarm(
        alarm_id="alarm-resolved-after-midnight",
        timestamp=datetime(
            2026,
            9,
            1,
            22,
            0,
            tzinfo=timezone.utc,
        ),
    )

    opened_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=AlarmTransitionType.OPENED,
            timestamp=opened.timestamp,
            source=INSTANCE_ID,
            state=AlarmState.ACTIVE,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=opened.timestamp,
        source=INSTANCE_ID,
        state=AlarmState.ACTIVE,
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=opened,
        transition=opened_transition,
    )

    resolved_at = datetime(
        2026,
        9,
        2,
        8,
        0,
        tzinfo=timezone.utc,
    )

    resolved = replace(
        opened,
        state=AlarmState.RESOLVED,
        resolved_at=resolved_at,
    )

    resolved_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=AlarmTransitionType.RESOLVED,
            timestamp=resolved_at,
            source=INSTANCE_ID,
            state=AlarmState.RESOLVED,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.RESOLVED,
        timestamp=resolved_at,
        source=INSTANCE_ID,
        state=AlarmState.RESOLVED,
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=resolved,
        transition=resolved_transition,
    )

    writer = JsonlEvidenceWriter(tmp_path)

    service = DailyAlarmContinuityService(
        repository,
        evidence_writer=writer,
    )

    result = service.catch_up(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        through=datetime(
            2026,
            9,
            2,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )

    carried = tuple(
        transition
        for transition in repository.list_transitions(
            opened.alarm_id
        )
        if (
            transition.transition_type
            is AlarmTransitionType.CARRIED_FORWARD
        )
    )

    assert result.carried_forward_count == 1
    assert len(carried) == 1

    assert carried[0].timestamp == datetime(
        2026,
        9,
        2,
        0,
        0,
        tzinfo=timezone.utc,
    )

    assert carried[0].state is AlarmState.ACTIVE

    current = repository.get_current(
        opened.alarm_id
    )

    assert current is not None
    assert current.state is AlarmState.RESOLVED
    assert current.resolved_at == resolved_at


def test_resolution_before_boundary_is_not_carried_forward(
    tmp_path,
) -> None:
    from dataclasses import replace

    from app.noc.history.alarm_transition import (
        AlarmTransition,
        make_alarm_transition_id,
    )
    from app.noc.history.jsonl_evidence_writer import (
        JsonlEvidenceWriter,
    )

    repository = InMemoryAlarmHistoryRepository()

    opened = make_alarm(
        alarm_id="alarm-resolved-before-midnight",
        timestamp=datetime(
            2026,
            9,
            1,
            20,
            0,
            tzinfo=timezone.utc,
        ),
    )

    opened_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=AlarmTransitionType.OPENED,
            timestamp=opened.timestamp,
            source=INSTANCE_ID,
            state=AlarmState.ACTIVE,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=opened.timestamp,
        source=INSTANCE_ID,
        state=AlarmState.ACTIVE,
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=opened,
        transition=opened_transition,
    )

    resolved_at = datetime(
        2026,
        9,
        1,
        23,
        30,
        tzinfo=timezone.utc,
    )

    resolved = replace(
        opened,
        state=AlarmState.RESOLVED,
        resolved_at=resolved_at,
    )

    resolved_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=AlarmTransitionType.RESOLVED,
            timestamp=resolved_at,
            source=INSTANCE_ID,
            state=AlarmState.RESOLVED,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.RESOLVED,
        timestamp=resolved_at,
        source=INSTANCE_ID,
        state=AlarmState.RESOLVED,
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=resolved,
        transition=resolved_transition,
    )

    writer = JsonlEvidenceWriter(tmp_path)

    service = DailyAlarmContinuityService(
        repository,
        evidence_writer=writer,
    )

    result = service.catch_up(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        through=datetime(
            2026,
            9,
            2,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )

    carried = tuple(
        transition
        for transition in repository.list_transitions(
            opened.alarm_id
        )
        if (
            transition.transition_type
            is AlarmTransitionType.CARRIED_FORWARD
        )
    )

    assert result.carried_forward_count == 0
    assert carried == ()

    current = repository.get_current(
        opened.alarm_id
    )

    assert current is not None
    assert current.state is AlarmState.RESOLVED


def test_catch_up_preserves_historical_state_across_boundaries(
    tmp_path,
) -> None:
    from dataclasses import replace

    from app.noc.history.alarm_transition import (
        AlarmTransition,
        make_alarm_transition_id,
    )
    from app.noc.history.jsonl_evidence_writer import (
        JsonlEvidenceWriter,
    )

    repository = InMemoryAlarmHistoryRepository()

    opened_at = datetime(
        2026,
        9,
        1,
        22,
        0,
        tzinfo=timezone.utc,
    )

    opened = make_alarm(
        alarm_id="alarm-historical-state",
        timestamp=opened_at,
    )

    opened_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=AlarmTransitionType.OPENED,
            timestamp=opened_at,
            source=INSTANCE_ID,
            state=AlarmState.ACTIVE,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=opened_at,
        source=INSTANCE_ID,
        state=AlarmState.ACTIVE,
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=opened,
        transition=opened_transition,
    )

    acknowledged_at = datetime(
        2026,
        9,
        3,
        8,
        0,
        tzinfo=timezone.utc,
    )

    acknowledged = replace(
        opened,
        state=AlarmState.ACKNOWLEDGED,
        acknowledged=True,
        acknowledged_by="operator",
        acknowledged_at=acknowledged_at,
    )

    acknowledged_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=AlarmTransitionType.ACKNOWLEDGED,
            timestamp=acknowledged_at,
            source=INSTANCE_ID,
            state=AlarmState.ACKNOWLEDGED,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.ACKNOWLEDGED,
        timestamp=acknowledged_at,
        source=INSTANCE_ID,
        state=AlarmState.ACKNOWLEDGED,
        actor="operator",
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=acknowledged,
        transition=acknowledged_transition,
    )

    resolved_at = datetime(
        2026,
        9,
        4,
        12,
        0,
        tzinfo=timezone.utc,
    )

    resolved = replace(
        acknowledged,
        state=AlarmState.RESOLVED,
        resolved_at=resolved_at,
    )

    resolved_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=AlarmTransitionType.RESOLVED,
            timestamp=resolved_at,
            source=INSTANCE_ID,
            state=AlarmState.RESOLVED,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.RESOLVED,
        timestamp=resolved_at,
        source=INSTANCE_ID,
        state=AlarmState.RESOLVED,
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=resolved,
        transition=resolved_transition,
    )

    writer = JsonlEvidenceWriter(tmp_path)

    service = DailyAlarmContinuityService(
        repository,
        evidence_writer=writer,
    )

    result = service.catch_up(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        through=datetime(
            2026,
            9,
            5,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )

    carried = tuple(
        transition
        for transition in repository.list_transitions(
            opened.alarm_id
        )
        if (
            transition.transition_type
            is AlarmTransitionType.CARRIED_FORWARD
        )
    )

    assert result.carried_forward_count == 3

    assert tuple(
        (
            transition.timestamp,
            transition.state,
        )
        for transition in carried
    ) == (
        (
            datetime(
                2026, 9, 2, 0, 0,
                tzinfo=timezone.utc,
            ),
            AlarmState.ACTIVE,
        ),
        (
            datetime(
                2026, 9, 3, 0, 0,
                tzinfo=timezone.utc,
            ),
            AlarmState.ACTIVE,
        ),
        (
            datetime(
                2026, 9, 4, 0, 0,
                tzinfo=timezone.utc,
            ),
            AlarmState.ACKNOWLEDGED,
        ),
    )

    assert repository.get_current(
        opened.alarm_id
    ) == resolved

    for day in ("02", "03", "04"):
        path = (
            tmp_path
            / "2026"
            / "09"
            / day
            / "alarm_transitions.jsonl"
        )

        assert path.exists()
        assert len(
            path.read_text(
                encoding="utf-8"
            ).splitlines()
        ) == 1


def test_sqlite_catch_up_preserves_historical_state_after_reopen(
    tmp_path,
) -> None:
    from dataclasses import replace

    from app.noc.history.alarm_transition import (
        AlarmTransition,
        make_alarm_transition_id,
    )
    from app.noc.history.jsonl_evidence_writer import (
        JsonlEvidenceWriter,
    )
    from app.noc.history.sqlite_alarm_repository import (
        SQLiteAlarmHistoryRepository,
    )
    from app.noc.history.sqlite_database import (
        SQLiteHistoryDatabase,
    )

    database_path = tmp_path / "history.sqlite3"
    evidence_path = tmp_path / "evidence"

    database = SQLiteHistoryDatabase(
        database_path
    )
    repository = SQLiteAlarmHistoryRepository(
        database
    )

    opened_at = datetime(
        2026,
        9,
        1,
        22,
        0,
        tzinfo=timezone.utc,
    )

    opened = make_alarm(
        alarm_id="alarm-sqlite-historical-state",
        timestamp=opened_at,
    )

    opened_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=AlarmTransitionType.OPENED,
            timestamp=opened_at,
            source=INSTANCE_ID,
            state=AlarmState.ACTIVE,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=opened_at,
        source=INSTANCE_ID,
        state=AlarmState.ACTIVE,
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=opened,
        transition=opened_transition,
    )

    acknowledged_at = datetime(
        2026,
        9,
        3,
        8,
        0,
        tzinfo=timezone.utc,
    )

    acknowledged = replace(
        opened,
        state=AlarmState.ACKNOWLEDGED,
        acknowledged=True,
        acknowledged_by="operator",
        acknowledged_at=acknowledged_at,
    )

    acknowledged_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=AlarmTransitionType.ACKNOWLEDGED,
            timestamp=acknowledged_at,
            source=INSTANCE_ID,
            state=AlarmState.ACKNOWLEDGED,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.ACKNOWLEDGED,
        timestamp=acknowledged_at,
        source=INSTANCE_ID,
        state=AlarmState.ACKNOWLEDGED,
        actor="operator",
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=acknowledged,
        transition=acknowledged_transition,
    )

    resolved_at = datetime(
        2026,
        9,
        4,
        12,
        0,
        tzinfo=timezone.utc,
    )

    resolved = replace(
        acknowledged,
        state=AlarmState.RESOLVED,
        resolved_at=resolved_at,
    )

    resolved_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=AlarmTransitionType.RESOLVED,
            timestamp=resolved_at,
            source=INSTANCE_ID,
            state=AlarmState.RESOLVED,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.RESOLVED,
        timestamp=resolved_at,
        source=INSTANCE_ID,
        state=AlarmState.RESOLVED,
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=resolved,
        transition=resolved_transition,
    )

    # Simulate process/repository restart.
    del repository
    del database

    reopened_database = SQLiteHistoryDatabase(
        database_path
    )
    reopened_repository = SQLiteAlarmHistoryRepository(
        reopened_database
    )

    writer = JsonlEvidenceWriter(
        evidence_path
    )

    service = DailyAlarmContinuityService(
        reopened_repository,
        evidence_writer=writer,
    )

    first = service.catch_up(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        through=datetime(
            2026,
            9,
            5,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )

    second = service.catch_up(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        through=datetime(
            2026,
            9,
            5,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )

    carried = tuple(
        transition
        for transition in reopened_repository.list_transitions(
            opened.alarm_id
        )
        if (
            transition.transition_type
            is AlarmTransitionType.CARRIED_FORWARD
        )
    )

    assert first.carried_forward_count == 3
    assert second.carried_forward_count == 3

    assert tuple(
        (
            transition.timestamp,
            transition.state,
        )
        for transition in carried
    ) == (
        (
            datetime(
                2026, 9, 2, 0, 0,
                tzinfo=timezone.utc,
            ),
            AlarmState.ACTIVE,
        ),
        (
            datetime(
                2026, 9, 3, 0, 0,
                tzinfo=timezone.utc,
            ),
            AlarmState.ACTIVE,
        ),
        (
            datetime(
                2026, 9, 4, 0, 0,
                tzinfo=timezone.utc,
            ),
            AlarmState.ACKNOWLEDGED,
        ),
    )

    assert reopened_repository.get_current(
        opened.alarm_id
    ) == resolved

    assert len(
        {
            transition.transition_id
            for transition in carried
        }
    ) == 3

    for day in ("02", "03", "04"):
        path = (
            evidence_path
            / "2026"
            / "09"
            / day
            / "alarm_transitions.jsonl"
        )

        assert path.exists()

        lines = path.read_text(
            encoding="utf-8"
        ).splitlines()

        assert len(lines) == 1


def test_acknowledged_exactly_at_boundary_carries_prior_active_state(
    tmp_path,
) -> None:
    from dataclasses import replace

    from app.noc.history.alarm_transition import (
        AlarmTransition,
        make_alarm_transition_id,
    )

    repository = InMemoryAlarmHistoryRepository()

    opened_at = datetime(
        2026,
        9,
        1,
        22,
        0,
        tzinfo=timezone.utc,
    )

    opened = make_alarm(
        alarm_id="alarm-ack-exact-boundary",
        timestamp=opened_at,
    )

    opened_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=AlarmTransitionType.OPENED,
            timestamp=opened_at,
            source=INSTANCE_ID,
            state=AlarmState.ACTIVE,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=opened_at,
        source=INSTANCE_ID,
        state=AlarmState.ACTIVE,
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=opened,
        transition=opened_transition,
    )

    boundary = datetime(
        2026,
        9,
        2,
        0,
        0,
        tzinfo=timezone.utc,
    )

    acknowledged = replace(
        opened,
        state=AlarmState.ACKNOWLEDGED,
        acknowledged=True,
        acknowledged_by="operator",
        acknowledged_at=boundary,
    )

    acknowledged_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=(
                AlarmTransitionType.ACKNOWLEDGED
            ),
            timestamp=boundary,
            source=INSTANCE_ID,
            state=AlarmState.ACKNOWLEDGED,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.ACKNOWLEDGED,
        timestamp=boundary,
        source=INSTANCE_ID,
        state=AlarmState.ACKNOWLEDGED,
        actor="operator",
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=acknowledged,
        transition=acknowledged_transition,
    )

    service = DailyAlarmContinuityService(
        repository
    )

    result = service.catch_up(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        through=datetime(
            2026,
            9,
            2,
            1,
            0,
            tzinfo=timezone.utc,
        ),
    )

    carried = tuple(
        transition
        for transition in repository.list_transitions(
            opened.alarm_id
        )
        if (
            transition.transition_type
            is AlarmTransitionType.CARRIED_FORWARD
        )
    )

    assert result.carried_forward_count == 1
    assert len(carried) == 1
    assert carried[0].timestamp == boundary
    assert carried[0].state is AlarmState.ACTIVE

    assert repository.get_current(
        opened.alarm_id
    ) == acknowledged


def test_resolved_exactly_at_boundary_carries_prior_acknowledged_state(
    tmp_path,
) -> None:
    from dataclasses import replace

    from app.noc.history.alarm_transition import (
        AlarmTransition,
        make_alarm_transition_id,
    )

    repository = InMemoryAlarmHistoryRepository()

    opened_at = datetime(
        2026,
        9,
        1,
        20,
        0,
        tzinfo=timezone.utc,
    )

    opened = make_alarm(
        alarm_id="alarm-resolve-exact-boundary",
        timestamp=opened_at,
    )

    opened_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=AlarmTransitionType.OPENED,
            timestamp=opened_at,
            source=INSTANCE_ID,
            state=AlarmState.ACTIVE,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=opened_at,
        source=INSTANCE_ID,
        state=AlarmState.ACTIVE,
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=opened,
        transition=opened_transition,
    )

    acknowledged_at = datetime(
        2026,
        9,
        1,
        23,
        0,
        tzinfo=timezone.utc,
    )

    acknowledged = replace(
        opened,
        state=AlarmState.ACKNOWLEDGED,
        acknowledged=True,
        acknowledged_by="operator",
        acknowledged_at=acknowledged_at,
    )

    acknowledged_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=(
                AlarmTransitionType.ACKNOWLEDGED
            ),
            timestamp=acknowledged_at,
            source=INSTANCE_ID,
            state=AlarmState.ACKNOWLEDGED,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.ACKNOWLEDGED,
        timestamp=acknowledged_at,
        source=INSTANCE_ID,
        state=AlarmState.ACKNOWLEDGED,
        actor="operator",
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=acknowledged,
        transition=acknowledged_transition,
    )

    boundary = datetime(
        2026,
        9,
        2,
        0,
        0,
        tzinfo=timezone.utc,
    )

    resolved = replace(
        acknowledged,
        state=AlarmState.RESOLVED,
        resolved_at=boundary,
    )

    resolved_transition = AlarmTransition(
        transition_id=make_alarm_transition_id(
            alarm_id=opened.alarm_id,
            transition_type=AlarmTransitionType.RESOLVED,
            timestamp=boundary,
            source=INSTANCE_ID,
            state=AlarmState.RESOLVED,
        ),
        alarm_id=opened.alarm_id,
        transition_type=AlarmTransitionType.RESOLVED,
        timestamp=boundary,
        source=INSTANCE_ID,
        state=AlarmState.RESOLVED,
    )

    repository.record_lifecycle(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        alarm=resolved,
        transition=resolved_transition,
    )

    service = DailyAlarmContinuityService(
        repository
    )

    result = service.catch_up(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        through=datetime(
            2026,
            9,
            2,
            1,
            0,
            tzinfo=timezone.utc,
        ),
    )

    carried = tuple(
        transition
        for transition in repository.list_transitions(
            opened.alarm_id
        )
        if (
            transition.transition_type
            is AlarmTransitionType.CARRIED_FORWARD
        )
    )

    assert result.carried_forward_count == 1
    assert len(carried) == 1
    assert carried[0].timestamp == boundary
    assert (
        carried[0].state
        is AlarmState.ACKNOWLEDGED
    )

    assert repository.get_current(
        opened.alarm_id
    ) == resolved
