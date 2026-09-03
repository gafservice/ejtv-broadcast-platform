from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, call

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.evidence_day_sealer import (
    EvidenceDaySealer,
)
from app.noc.history.historical_range_repository import (
    HistoricalRangeRepository,
)
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
    sealer = Mock(
        spec=EvidenceDaySealer
    )

    continuity.catch_up.side_effect = (
        lambda **_: calls.append("continuity")
    )

    reconciliation.reconcile_between.side_effect = (
        lambda **_: calls.append("reconciliation")
    )
    sealer.seal_day.side_effect = (
        lambda *_: calls.append("sealing")
    )

    runtime = DailyHistoryMaintenanceRuntime(
        continuity_service=continuity,
        reconciliation_service=reconciliation,
        evidence_day_sealer=sealer,
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
        "reconciliation",
        "sealing",
    ]

    continuity.catch_up.assert_called_once_with(
        node_id=node_id,
        instance_id=instance_id,
        through=boundary,
    )

    mature_day = (
        boundary.date()
        - timedelta(days=2)
    )

    mature_day_start = datetime.combine(
        mature_day,
        datetime.min.time(),
        tzinfo=timezone.utc,
    )

    mature_day_end = (
        mature_day_start
        + timedelta(days=1)
    )

    assert reconciliation.reconcile_between.call_count == 2

    recent_call = (
        reconciliation.reconcile_between.call_args_list[0]
    )
    exact_day_call = (
        reconciliation.reconcile_between.call_args_list[1]
    )

    assert recent_call.kwargs == {
        "start": boundary - timedelta(hours=48),
        "end": boundary + timedelta(microseconds=1),
        "node_id": node_id,
        "instance_id": instance_id,
    }

    assert exact_day_call.kwargs == {
        "start": mature_day_start,
        "end": mature_day_end,
        "node_id": node_id,
        "instance_id": instance_id,
    }

    sealer.seal_day.assert_called_once_with(
        mature_day
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
    sealer = Mock(
        spec=EvidenceDaySealer
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
        evidence_day_sealer=sealer,
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

    mature_day = (
        boundary.date()
        - timedelta(days=2)
    )

    mature_day_end = datetime.combine(
        mature_day + timedelta(days=1),
        datetime.min.time(),
        tzinfo=timezone.utc,
    )

    assert calls == [
        (
            "continuity",
            boundary,
        ),
        (
            "reconciliation",
            boundary + timedelta(microseconds=1),
        ),
        (
            "reconciliation",
            mature_day_end,
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
    evidence_day_sealer = EvidenceDaySealer(
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
        evidence_day_sealer=evidence_day_sealer,
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
    sealer = Mock(
        spec=EvidenceDaySealer
    )

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        DailyHistoryMaintenanceRuntime(
            continuity_service=continuity,
            reconciliation_service=reconciliation,
        evidence_day_sealer=sealer,
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
    sealer = Mock(
        spec=EvidenceDaySealer
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
        evidence_day_sealer=sealer,
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


def test_run_once_catches_up_all_missing_mature_days_chronologically() -> None:
    continuity = Mock(
        spec=DailyAlarmContinuityService
    )
    reconciliation = Mock(
        spec=EvidenceReconciliationService
    )
    sealer = Mock(
        spec=EvidenceDaySealer
    )

    historical_range = Mock(
        spec=HistoricalRangeRepository
    )
    historical_range.first_historical_timestamp.return_value = datetime(
        2026,
        9,
        1,
        12,
        30,
        tzinfo=timezone.utc,
    )

    sealed_days = {
        # Deliberately leave 2026-09-02 missing.
        # This proves that an interior gap is repaired even though
        # a later day is already sealed.
        datetime(
            2026,
            9,
            3,
            tzinfo=timezone.utc,
        ).date(),
    }

    sealer.verify_day.side_effect = (
        lambda day: day in sealed_days
    )

    runtime = DailyHistoryMaintenanceRuntime(
        continuity_service=continuity,
        reconciliation_service=reconciliation,
        evidence_day_sealer=sealer,
        historical_range_repository=historical_range,
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

    through = datetime(
        2026,
        9,
        7,
        10,
        0,
        tzinfo=timezone.utc,
    )

    runtime.run_once(
        node_id=node_id,
        instance_id=instance_id,
        through=through,
    )

    historical_range.first_historical_timestamp.assert_called_once_with(
        node_id=node_id,
        instance_id=instance_id,
    )

    expected_missing_days = [
        datetime(2026, 9, 1, tzinfo=timezone.utc).date(),
        datetime(2026, 9, 2, tzinfo=timezone.utc).date(),
        datetime(2026, 9, 4, tzinfo=timezone.utc).date(),
        datetime(2026, 9, 5, tzinfo=timezone.utc).date(),
    ]

    assert sealer.seal_day.call_args_list == [
        call(day)
        for day in expected_missing_days
    ]

    exact_day_calls = (
        reconciliation.reconcile_between.call_args_list[1:]
    )

    assert [
        (
            item.kwargs["start"],
            item.kwargs["end"],
        )
        for item in exact_day_calls
    ] == [
        (
            datetime(
                2026,
                9,
                day,
                0,
                0,
                tzinfo=timezone.utc,
            ),
            datetime(
                2026,
                9,
                day + 1,
                0,
                0,
                tzinfo=timezone.utc,
            ),
        )
        for day in (1, 2, 4, 5)
    ]


def test_mature_day_conflict_stops_before_reconciliation() -> None:
    from app.noc.history.evidence_day_sealer import (
        EvidenceSealConflictError,
    )

    continuity = Mock(
        spec=DailyAlarmContinuityService
    )
    reconciliation = Mock(
        spec=EvidenceReconciliationService
    )
    sealer = Mock(
        spec=EvidenceDaySealer
    )
    historical_range = Mock(
        spec=HistoricalRangeRepository
    )

    first_timestamp = datetime(
        2026,
        9,
        1,
        12,
        30,
        tzinfo=timezone.utc,
    )

    historical_range.first_historical_timestamp.return_value = (
        first_timestamp
    )

    sealer.verify_day.return_value = False

    sealer.assert_day_can_be_finalized.side_effect = (
        EvidenceSealConflictError(
            "existing manifest does not match current evidence"
        )
    )

    runtime = DailyHistoryMaintenanceRuntime(
        continuity_service=continuity,
        reconciliation_service=reconciliation,
        evidence_day_sealer=sealer,
        historical_range_repository=historical_range,
    )

    node_id = NodeId(
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

    instance_id = NodeInstanceId(
        "streaming-primary"
    )

    through = datetime(
        2026,
        9,
        7,
        10,
        0,
        tzinfo=timezone.utc,
    )

    import pytest

    with pytest.raises(
        EvidenceSealConflictError
    ):
        runtime.catch_up_mature_days(
            node_id=node_id,
            instance_id=instance_id,
            through=through,
        )

    sealer.verify_day.assert_called_once_with(
        first_timestamp.date()
    )

    sealer.assert_day_can_be_finalized.assert_called_once_with(
        first_timestamp.date()
    )

    reconciliation.reconcile_between.assert_not_called()
    sealer.seal_day.assert_not_called()
