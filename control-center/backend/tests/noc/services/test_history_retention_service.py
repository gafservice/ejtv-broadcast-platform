from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, call

import pytest

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.evidence_day_sealer import (
    EvidenceDaySealer,
)
from app.noc.history.history_retention_repository import (
    HistoryRetentionRepository,
    HistoryRetentionResult,
)
from app.noc.history.managed_history_repository import (
    ManagedHistoryRepository,
)
from app.noc.services.history_retention_service import (
    HistoryRetentionBlockedError,
    HistoryRetentionService,
)


UTC = timezone.utc

NODE = NodeId(
    id="streaming-core",
    name="streaming-core",
    display_name="Streaming Core",
    created_at=datetime(2026, 9, 1, tzinfo=UTC),
)

INSTANCE = NodeInstanceId(
    "streaming-primary"
)

CUTOFF = datetime(
    2026,
    9,
    5,
    tzinfo=UTC,
)


def _service(
    *,
    managed_day=None,
    verify_side_effect=None,
):
    retention_repository = Mock(
        spec=HistoryRetentionRepository
    )
    retention_repository.prune_before.return_value = (
        HistoryRetentionResult(
            events_deleted=3,
            alarm_transitions_deleted=4,
            alarms_deleted=2,
        )
    )

    managed_history_repository = Mock(
        spec=ManagedHistoryRepository
    )
    managed_history_repository.get_managed_since_day.return_value = (
        managed_day
    )

    evidence_day_sealer = Mock(
        spec=EvidenceDaySealer
    )

    if verify_side_effect is None:
        evidence_day_sealer.verify_day.return_value = True
    else:
        evidence_day_sealer.verify_day.side_effect = (
            verify_side_effect
        )

    service = HistoryRetentionService(
        retention_repository=retention_repository,
        managed_history_repository=(
            managed_history_repository
        ),
        evidence_day_sealer=evidence_day_sealer,
    )

    return (
        service,
        retention_repository,
        managed_history_repository,
        evidence_day_sealer,
    )


def test_no_managed_anchor_returns_empty_result() -> None:
    (
        service,
        retention_repository,
        _,
        evidence_day_sealer,
    ) = _service(
        managed_day=None
    )

    result = service.prune_before(
        node_id=NODE,
        instance_id=INSTANCE,
        cutoff=CUTOFF,
    )

    assert result == HistoryRetentionResult(
        events_deleted=0,
        alarm_transitions_deleted=0,
        alarms_deleted=0,
    )

    retention_repository.prune_before.assert_not_called()
    evidence_day_sealer.verify_day.assert_not_called()


def test_all_days_must_verify_before_repository_prune() -> None:
    first_day = datetime(
        2026,
        9,
        2,
        tzinfo=UTC,
    ).date()

    (
        service,
        retention_repository,
        _,
        evidence_day_sealer,
    ) = _service(
        managed_day=first_day
    )

    result = service.prune_before(
        node_id=NODE,
        instance_id=INSTANCE,
        cutoff=CUTOFF,
    )

    assert result.events_deleted == 3
    assert result.alarm_transitions_deleted == 4
    assert result.alarms_deleted == 2

    assert evidence_day_sealer.verify_day.call_args_list == [
        call(datetime(2026, 9, 2, tzinfo=UTC).date()),
        call(datetime(2026, 9, 3, tzinfo=UTC).date()),
        call(datetime(2026, 9, 4, tzinfo=UTC).date()),
    ]

    retention_repository.prune_before.assert_called_once_with(
        node_id=NODE,
        instance_id=INSTANCE,
        cutoff=CUTOFF,
    )


def test_invalid_day_blocks_retention_before_any_delete() -> None:
    first_day = datetime(
        2026,
        9,
        2,
        tzinfo=UTC,
    ).date()

    valid_days = {
        datetime(2026, 9, 2, tzinfo=UTC).date(): True,
        datetime(2026, 9, 3, tzinfo=UTC).date(): False,
    }

    (
        service,
        retention_repository,
        _,
        evidence_day_sealer,
    ) = _service(
        managed_day=first_day,
        verify_side_effect=lambda day: valid_days.get(
            day,
            True,
        ),
    )

    with pytest.raises(
        HistoryRetentionBlockedError,
        match="2026-09-03",
    ):
        service.prune_before(
            node_id=NODE,
            instance_id=INSTANCE,
            cutoff=CUTOFF,
        )

    retention_repository.prune_before.assert_not_called()

    assert evidence_day_sealer.verify_day.call_args_list == [
        call(datetime(2026, 9, 2, tzinfo=UTC).date()),
        call(datetime(2026, 9, 3, tzinfo=UTC).date()),
    ]


def test_cutoff_day_itself_is_not_required_to_verify() -> None:
    first_day = datetime(
        2026,
        9,
        4,
        tzinfo=UTC,
    ).date()

    (
        service,
        _,
        _,
        evidence_day_sealer,
    ) = _service(
        managed_day=first_day
    )

    service.prune_before(
        node_id=NODE,
        instance_id=INSTANCE,
        cutoff=CUTOFF,
    )

    evidence_day_sealer.verify_day.assert_called_once_with(
        datetime(2026, 9, 4, tzinfo=UTC).date()
    )


@pytest.mark.parametrize(
    "first_day",
    (
        datetime(2026, 9, 5, tzinfo=UTC).date(),
        datetime(2026, 9, 6, tzinfo=UTC).date(),
    ),
)
def test_anchor_at_or_after_cutoff_is_noop(
    first_day,
) -> None:
    (
        service,
        retention_repository,
        _,
        evidence_day_sealer,
    ) = _service(
        managed_day=first_day
    )

    result = service.prune_before(
        node_id=NODE,
        instance_id=INSTANCE,
        cutoff=CUTOFF,
    )

    assert result == HistoryRetentionResult(
        events_deleted=0,
        alarm_transitions_deleted=0,
        alarms_deleted=0,
    )

    evidence_day_sealer.verify_day.assert_not_called()
    retention_repository.prune_before.assert_not_called()


def test_cutoff_must_be_timezone_aware() -> None:
    service, _, _, _ = _service(
        managed_day=None
    )

    with pytest.raises(
        ValueError,
        match="cutoff must be timezone-aware",
    ):
        service.prune_before(
            node_id=NODE,
            instance_id=INSTANCE,
            cutoff=datetime(2026, 9, 5),
        )


def test_cutoff_must_be_utc() -> None:
    service, _, _, _ = _service(
        managed_day=None
    )

    with pytest.raises(
        ValueError,
        match="cutoff must be expressed in UTC",
    ):
        service.prune_before(
            node_id=NODE,
            instance_id=INSTANCE,
            cutoff=datetime(
                2026,
                9,
                5,
                tzinfo=timezone(
                    timedelta(hours=-6)
                ),
            ),
        )


def test_cutoff_must_be_utc_midnight() -> None:
    service, _, _, _ = _service(
        managed_day=None
    )

    with pytest.raises(
        ValueError,
        match="cutoff must be aligned",
    ):
        service.prune_before(
            node_id=NODE,
            instance_id=INSTANCE,
            cutoff=datetime(
                2026,
                9,
                5,
                0,
                0,
                1,
                tzinfo=UTC,
            ),
        )
