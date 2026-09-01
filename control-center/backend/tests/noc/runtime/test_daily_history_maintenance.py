from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.daily_history_maintenance import (
    DailyHistoryMaintenanceRuntime,
)
from app.noc.services.daily_alarm_continuity_service import (
    DailyAlarmContinuityService,
)
from app.noc.services.evidence_reconciliation_service import (
    EvidenceReconciliationService,
)


def test_next_utc_boundary() -> None:
    now = datetime(
        2026,
        9,
        1,
        23,
        59,
        59,
        tzinfo=timezone.utc,
    )

    boundary = (
        DailyHistoryMaintenanceRuntime
        .next_utc_boundary(now)
    )

    assert boundary == datetime(
        2026,
        9,
        2,
        0,
        0,
        tzinfo=timezone.utc,
    )


def test_next_utc_boundary_from_non_utc_timezone() -> None:
    costa_rica = timezone(
        -timedelta(hours=6)
    )

    now = datetime(
        2026,
        9,
        1,
        17,
        30,
        tzinfo=costa_rica,
    )

    boundary = (
        DailyHistoryMaintenanceRuntime
        .next_utc_boundary(now)
    )

    assert boundary == datetime(
        2026,
        9,
        2,
        0,
        0,
        tzinfo=timezone.utc,
    )


def test_run_once_executes_continuity_before_reconciliation() -> None:
    calls = []

    continuity = Mock(
        spec=DailyAlarmContinuityService
    )
    reconciliation = Mock(
        spec=EvidenceReconciliationService
    )

    continuity.catch_up.side_effect = (
        lambda **_: calls.append("continuity")
    )

    reconciliation.reconcile_between.side_effect = (
        lambda **_: calls.append("reconciliation")
    )

    runtime = DailyHistoryMaintenanceRuntime(
        continuity_service=continuity,
        reconciliation_service=reconciliation,
    )

    node_id = NodeId(
        id="streaming-core",
        name="streaming-core",
        display_name="Streaming Core",
        created_at=datetime(
            2026,
            9,
            1,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )
    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    boundary = datetime(
        2026,
        9,
        2,
        0,
        0,
        tzinfo=timezone.utc,
    )

    runtime.run_once(
        node_id=node_id,
        instance_id=instance_id,
        through=boundary,
    )

    assert calls == [
        "continuity",
        "reconciliation",
    ]

    continuity.catch_up.assert_called_once_with(
        node_id=node_id,
        instance_id=instance_id,
        through=boundary,
    )

    reconciliation.reconcile_between.assert_called_once_with(
        start=boundary - timedelta(hours=48),
        end=boundary + timedelta(microseconds=1),
        node_id=node_id,
        instance_id=instance_id,
    )


def test_run_forever_executes_at_next_utc_boundary(
    monkeypatch,
) -> None:
    import asyncio

    calls = []

    continuity = Mock(
        spec=DailyAlarmContinuityService
    )
    reconciliation = Mock(
        spec=EvidenceReconciliationService
    )

    continuity.catch_up.side_effect = (
        lambda **kwargs: calls.append(
            (
                "continuity",
                kwargs["through"],
            )
        )
    )

    reconciliation.reconcile_between.side_effect = (
        lambda **kwargs: calls.append(
            (
                "reconciliation",
                kwargs["end"],
            )
        )
    )

    times = iter(
        [
            datetime(
                2026,
                9,
                1,
                23,
                59,
                59,
                tzinfo=timezone.utc,
            ),
            datetime(
                2026,
                9,
                2,
                0,
                0,
                tzinfo=timezone.utc,
            ),
        ]
    )

    runtime = DailyHistoryMaintenanceRuntime(
        continuity_service=continuity,
        reconciliation_service=reconciliation,
        clock=lambda: next(times),
    )

    node_id = NodeId(
        id="streaming-core",
        name="streaming-core",
        display_name="Streaming Core",
        created_at=datetime(
            2026,
            9,
            1,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )

    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    boundary = datetime(
        2026,
        9,
        2,
        0,
        0,
        tzinfo=timezone.utc,
    )

    sleep_calls = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

        if len(sleep_calls) > 1:
            raise asyncio.CancelledError

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    async def exercise() -> None:
        try:
            await runtime.run_forever(
                node_id=node_id,
                instance_id=instance_id,
            )
        except (
            asyncio.CancelledError,
            StopIteration,
        ):
            pass

    asyncio.run(exercise())

    assert sleep_calls[0] == 1.0

    assert calls == [
        (
            "continuity",
            boundary,
        ),
        (
            "reconciliation",
            boundary + timedelta(microseconds=1),
        ),
    ]


def test_daily_boundary_persists_carried_forward_and_writes_new_day_jsonl(
    tmp_path,
) -> None:
    from app.noc.history.alarm_transition import (
        AlarmTransition,
        AlarmTransitionType,
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
    from app.noc.services.daily_alarm_continuity_service import (
        DailyAlarmContinuityService,
    )
    from app.noc.services.evidence_reconciliation_service import (
        EvidenceReconciliationService,
    )
    from app.noc.history.sqlite_event_repository import (
        SQLiteEventHistoryRepository,
    )
    from app.noc.domain.node_alarm import (
        AlarmRecord,
        AlarmSeverity,
        AlarmState,
    )

    node_id = NodeId(
        id="streaming-core",
        name="streaming-core",
        display_name="Streaming Core",
        created_at=datetime(
            2026,
            9,
            1,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )

    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    db = SQLiteHistoryDatabase(
        tmp_path / "history.db"
    )

    alarm_repo = SQLiteAlarmHistoryRepository(
        db
    )

    event_repo = SQLiteEventHistoryRepository(
        db
    )

    evidence_writer = JsonlEvidenceWriter(
        tmp_path / "evidence"
    )

    continuity_service = DailyAlarmContinuityService(
        alarm_repo
    )

    reconciliation_service = EvidenceReconciliationService(
        event_repository=event_repo,
        alarm_repository=alarm_repo,
        evidence_writer=evidence_writer,
    )

    opened_at = datetime(
        2026,
        9,
        1,
        22,
        0,
        tzinfo=timezone.utc,
    )

    alarm = AlarmRecord(
        alarm_id="alarm-cross-midnight-001",
        alarm_type="TEST_CROSS_MIDNIGHT",
        severity=AlarmSeverity.WARNING,
        state=AlarmState.ACTIVE,
        timestamp=opened_at,
        source=instance_id,
        title="Cross midnight",
        description="Test alarm",
    )

    opened_transition = AlarmTransition(
        transition_id="opened-cross-midnight-001",
        alarm_id=alarm.alarm_id,
        transition_type=AlarmTransitionType.OPENED,
        timestamp=opened_at,
        source=instance_id,
        state=AlarmState.ACTIVE,
    )

    alarm_repo.record_lifecycle(
        node_id=node_id,
        instance_id=instance_id,
        alarm=alarm,
        transition=opened_transition,
    )

    runtime = DailyHistoryMaintenanceRuntime(
        continuity_service=continuity_service,
        reconciliation_service=reconciliation_service,
    )

    boundary = datetime(
        2026,
        9,
        2,
        0,
        0,
        tzinfo=timezone.utc,
    )

    runtime.run_once(
        node_id=node_id,
        instance_id=instance_id,
        through=boundary,
    )

    transitions = alarm_repo.list_transitions(
        alarm.alarm_id
    )

    carried = [
        item
        for item in transitions
        if item.transition_type
        == AlarmTransitionType.CARRIED_FORWARD
    ]

    assert len(carried) == 1
    assert carried[0].timestamp == boundary
    assert carried[0].state == AlarmState.ACTIVE
    assert carried[0].alarm_id == alarm.alarm_id

    evidence_file = (
        tmp_path
        / "evidence"
        / "2026"
        / "09"
        / "02"
        / "alarm_transitions.jsonl"
    )

    assert evidence_file.exists()

    lines = [
        line
        for line in evidence_file.read_text().splitlines()
        if line.strip()
    ]

    assert len(lines) == 1

    import json

    payload = json.loads(lines[0])

    assert payload["alarm_id"] == alarm.alarm_id
    assert (
        payload["transition_type"]
        == AlarmTransitionType.CARRIED_FORWARD.value
    )
    assert payload["timestamp"].startswith(
        "2026-09-02T00:00:00"
    )


def test_retry_delay_must_be_positive() -> None:
    import pytest

    continuity = Mock(
        spec=DailyAlarmContinuityService
    )
    reconciliation = Mock(
        spec=EvidenceReconciliationService
    )

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        DailyHistoryMaintenanceRuntime(
            continuity_service=continuity,
            reconciliation_service=reconciliation,
            retry_delay_seconds=0,
        )


def test_run_forever_retries_same_boundary_after_failure(
    monkeypatch,
) -> None:
    import asyncio

    continuity = Mock(
        spec=DailyAlarmContinuityService
    )
    reconciliation = Mock(
        spec=EvidenceReconciliationService
    )

    now = datetime(
        2026,
        9,
        1,
        23,
        59,
        59,
        tzinfo=timezone.utc,
    )

    boundary = datetime(
        2026,
        9,
        2,
        0,
        0,
        0,
        tzinfo=timezone.utc,
    )

    runtime = DailyHistoryMaintenanceRuntime(
        continuity_service=continuity,
        reconciliation_service=reconciliation,
        clock=lambda: now,
        retry_delay_seconds=7.0,
    )

    node_id = NodeId(
        id="streaming-core",
        name="streaming-core",
        display_name="Streaming Core",
        created_at=datetime(
            2026,
            9,
            1,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )

    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    run_boundaries = []

    def fake_run_once(
        *,
        node_id,
        instance_id,
        through,
    ) -> None:
        run_boundaries.append(through)

        if len(run_boundaries) == 1:
            raise RuntimeError(
                "simulated maintenance failure"
            )

    runtime.run_once = fake_run_once

    sleep_calls = []

    async def fake_sleep(
        delay: float,
    ) -> None:
        sleep_calls.append(delay)

        # 1: espera hasta medianoche
        # 2: retry de 7 segundos
        # Después del segundo run_once exitoso,
        # el runtime vuelve al outer loop.
        # Cancelamos en la siguiente espera.
        if len(sleep_calls) >= 3:
            raise asyncio.CancelledError

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    async def exercise() -> None:
        try:
            await runtime.run_forever(
                node_id=node_id,
                instance_id=instance_id,
            )
        except asyncio.CancelledError:
            pass

    asyncio.run(exercise())

    assert sleep_calls[:2] == [
        1.0,
        7.0,
    ]

    assert run_boundaries == [
        boundary,
        boundary,
    ]
