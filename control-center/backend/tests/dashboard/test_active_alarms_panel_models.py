"""Tests para los modelos de presentación de ACTIVE ALARMS."""

from datetime import UTC, datetime

import pytest

from app.dashboard.models import (
    ActiveAlarmRowData,
    ActiveAlarmsPanelData,
)


OPENED_AT = datetime(
    2026,
    8,
    21,
    23,
    15,
    30,
    tzinfo=UTC,
)


def make_alarm(
    *,
    alarm_id: str = "alarm-001",
) -> ActiveAlarmRowData:
    return ActiveAlarmRowData(
        alarm_id=alarm_id,
        alarm_type="NODE_HEALTH_DEGRADED",
        severity="CRITICAL",
        state="ACTIVE",
        message="Node health degraded to CRITICAL",
        opened_at=OPENED_AT,
    )


def test_alarm_row_accepts_valid_data() -> None:
    alarm = make_alarm()

    assert alarm.alarm_id == "alarm-001"
    assert alarm.alarm_type == "NODE_HEALTH_DEGRADED"
    assert alarm.severity == "CRITICAL"
    assert alarm.state == "ACTIVE"
    assert alarm.message == "Node health degraded to CRITICAL"
    assert alarm.opened_at == OPENED_AT


@pytest.mark.parametrize(
    "field_name",
    (
        "alarm_id",
        "alarm_type",
        "severity",
        "state",
        "message",
    ),
)
def test_alarm_row_rejects_empty_text(
    field_name: str,
) -> None:
    kwargs = {
        "alarm_id": "alarm-001",
        "alarm_type": "NODE_HEALTH_DEGRADED",
        "severity": "CRITICAL",
        "state": "ACTIVE",
        "message": "Node health degraded to CRITICAL",
        "opened_at": OPENED_AT,
    }

    kwargs[field_name] = "   "

    with pytest.raises(ValueError):
        ActiveAlarmRowData(**kwargs)


@pytest.mark.parametrize(
    "field_name",
    (
        "alarm_id",
        "alarm_type",
        "severity",
        "state",
        "message",
    ),
)
def test_alarm_row_rejects_non_text(
    field_name: str,
) -> None:
    kwargs = {
        "alarm_id": "alarm-001",
        "alarm_type": "NODE_HEALTH_DEGRADED",
        "severity": "CRITICAL",
        "state": "ACTIVE",
        "message": "Node health degraded to CRITICAL",
        "opened_at": OPENED_AT,
    }

    kwargs[field_name] = 123

    with pytest.raises(ValueError):
        ActiveAlarmRowData(**kwargs)


def test_alarm_row_normalizes_text() -> None:
    alarm = ActiveAlarmRowData(
        alarm_id=" alarm-001 ",
        alarm_type=" NODE_HEALTH_DEGRADED ",
        severity=" CRITICAL ",
        state=" ACTIVE ",
        message=" Node health degraded to CRITICAL ",
        opened_at=OPENED_AT,
    )

    assert alarm.alarm_id == "alarm-001"
    assert alarm.alarm_type == "NODE_HEALTH_DEGRADED"
    assert alarm.severity == "CRITICAL"
    assert alarm.state == "ACTIVE"
    assert alarm.message == "Node health degraded to CRITICAL"


def test_alarm_row_rejects_invalid_opened_at() -> None:
    with pytest.raises(ValueError):
        ActiveAlarmRowData(
            alarm_id="alarm-001",
            alarm_type="NODE_HEALTH_DEGRADED",
            severity="CRITICAL",
            state="ACTIVE",
            message="Node health degraded to CRITICAL",
            opened_at="2026-08-21",  # type: ignore[arg-type]
        )


def test_alarm_row_rejects_naive_opened_at() -> None:
    with pytest.raises(ValueError):
        ActiveAlarmRowData(
            alarm_id="alarm-001",
            alarm_type="NODE_HEALTH_DEGRADED",
            severity="CRITICAL",
            state="ACTIVE",
            message="Node health degraded to CRITICAL",
            opened_at=datetime(
                2026,
                8,
                21,
                23,
                15,
                30,
            ),
        )


def test_panel_accepts_alarm_tuple() -> None:
    alarms = (
        make_alarm(
            alarm_id="alarm-001",
        ),
        make_alarm(
            alarm_id="alarm-002",
        ),
    )

    panel = ActiveAlarmsPanelData(
        alarms=alarms,
    )

    assert panel.alarms == alarms
    assert panel.alarm_count == 2
    assert panel.is_empty is False


def test_panel_accepts_empty_tuple() -> None:
    panel = ActiveAlarmsPanelData(
        alarms=(),
    )

    assert panel.alarm_count == 0
    assert panel.is_empty is True


def test_panel_rejects_non_tuple() -> None:
    with pytest.raises(ValueError):
        ActiveAlarmsPanelData(
            alarms=[make_alarm()],  # type: ignore[arg-type]
        )


def test_panel_rejects_invalid_items() -> None:
    with pytest.raises(ValueError):
        ActiveAlarmsPanelData(
            alarms=(object(),),  # type: ignore[arg-type]
        )


def test_panel_rejects_duplicate_alarm_ids() -> None:
    with pytest.raises(ValueError):
        ActiveAlarmsPanelData(
            alarms=(
                make_alarm(
                    alarm_id="alarm-001",
                ),
                make_alarm(
                    alarm_id="alarm-001",
                ),
            )
        )
