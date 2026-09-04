from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.noc.history.history_retention_repository import (
    HistoryRetentionRepository,
    HistoryRetentionResult,
)


class _RetentionRepository:
    def prune_before(
        self,
        *,
        node_id,
        instance_id,
        cutoff,
    ) -> HistoryRetentionResult:
        return HistoryRetentionResult(
            events_deleted=0,
            alarm_transitions_deleted=0,
            alarms_deleted=0,
        )


def test_runtime_protocol_accepts_compatible_repository() -> None:
    assert isinstance(
        _RetentionRepository(),
        HistoryRetentionRepository,
    )


def test_retention_result_accepts_non_negative_counts() -> None:
    result = HistoryRetentionResult(
        events_deleted=3,
        alarm_transitions_deleted=7,
        alarms_deleted=2,
    )

    assert result.events_deleted == 3
    assert result.alarm_transitions_deleted == 7
    assert result.alarms_deleted == 2


@pytest.mark.parametrize(
    "field_name",
    (
        "events_deleted",
        "alarm_transitions_deleted",
        "alarms_deleted",
    ),
)
def test_retention_result_rejects_negative_counts(
    field_name: str,
) -> None:
    values = {
        "events_deleted": 0,
        "alarm_transitions_deleted": 0,
        "alarms_deleted": 0,
    }

    values[field_name] = -1

    with pytest.raises(
        ValueError,
        match=f"{field_name} must not be negative",
    ):
        HistoryRetentionResult(**values)


@pytest.mark.parametrize(
    "invalid",
    (
        1.5,
        "1",
        True,
        None,
    ),
)
def test_retention_result_rejects_non_integer_counts(
    invalid,
) -> None:
    with pytest.raises(
        TypeError,
        match="events_deleted must be an int",
    ):
        HistoryRetentionResult(
            events_deleted=invalid,
            alarm_transitions_deleted=0,
            alarms_deleted=0,
        )


def test_protocol_method_shape_can_be_called() -> None:
    repository = _RetentionRepository()

    result = repository.prune_before(
        node_id=object(),
        instance_id=object(),
        cutoff=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
    )

    assert result == HistoryRetentionResult(
        events_deleted=0,
        alarm_transitions_deleted=0,
        alarms_deleted=0,
    )
