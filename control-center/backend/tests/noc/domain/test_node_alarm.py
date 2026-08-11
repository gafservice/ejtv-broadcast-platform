"""Tests for NodeAlarm.

ENG-013B — Node SDK
NCS reference: 18-NODE-ALARM.md
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
    NodeAlarm,
)
from app.noc.domain.node_instance import NodeInstanceId


def now() -> datetime:
    return datetime.now(timezone.utc)


def make_alarm(
    *,
    alarm_id: str = "alm-001",
    alarm_type: str = "CPU_HIGH",
    severity: AlarmSeverity = AlarmSeverity.MAJOR,
    state: AlarmState = AlarmState.ACTIVE,
    acknowledged: bool = False,
    acknowledged_by: str | None = None,
    acknowledged_at: datetime | None = None,
    resolved_at: datetime | None = None,
    closed_at: datetime | None = None,
) -> AlarmRecord:
    return AlarmRecord(
        alarm_id=alarm_id,
        alarm_type=alarm_type,
        severity=severity,
        state=state,
        timestamp=now(),
        source=NodeInstanceId("streaming-primary"),
        title="CPU usage exceeded threshold",
        description="CPU utilization is above the configured threshold.",
        acknowledged=acknowledged,
        acknowledged_by=acknowledged_by,
        acknowledged_at=acknowledged_at,
        resolved_at=resolved_at,
        closed_at=closed_at,
        attributes={
            "threshold": "95",
            "current_value": "98.2",
        },
    )


def test_alarm_severity_contains_canonical_values() -> None:
    expected = {
        "INFO",
        "WARNING",
        "MINOR",
        "MAJOR",
        "CRITICAL",
    }

    assert {
        value.value for value in AlarmSeverity
    } == expected


def test_alarm_state_contains_canonical_values() -> None:
    expected = {
        "ACTIVE",
        "ACKNOWLEDGED",
        "RESOLVED",
        "CLOSED",
    }

    assert {
        value.value for value in AlarmState
    } == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("info", AlarmSeverity.INFO),
        (" warning ", AlarmSeverity.WARNING),
        ("minor", AlarmSeverity.MINOR),
        ("major", AlarmSeverity.MAJOR),
        ("critical", AlarmSeverity.CRITICAL),
    ],
)
def test_alarm_severity_from_value(
    raw: str,
    expected: AlarmSeverity,
) -> None:
    assert AlarmSeverity.from_value(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("active", AlarmState.ACTIVE),
        (" acknowledged ", AlarmState.ACKNOWLEDGED),
        ("resolved", AlarmState.RESOLVED),
        ("closed", AlarmState.CLOSED),
    ],
)
def test_alarm_state_from_value(
    raw: str,
    expected: AlarmState,
) -> None:
    assert AlarmState.from_value(raw) is expected


def test_alarm_record_can_be_created() -> None:
    alarm = make_alarm()

    assert alarm.alarm_id == "alm-001"
    assert alarm.alarm_type == "CPU_HIGH"
    assert alarm.state is AlarmState.ACTIVE


def test_alarm_record_normalizes_strings() -> None:
    alarm = AlarmRecord(
        alarm_id="  alm-001  ",
        alarm_type="  cpu_high  ",
        severity=AlarmSeverity.MAJOR,
        state=AlarmState.ACTIVE,
        timestamp=now(),
        source=NodeInstanceId("streaming-primary"),
        title="  CPU high  ",
        description="  CPU exceeded threshold.  ",
    )

    assert alarm.alarm_id == "alm-001"
    assert alarm.alarm_type == "CPU_HIGH"
    assert alarm.title == "CPU high"
    assert alarm.description == "CPU exceeded threshold."


def test_alarm_record_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError):
        AlarmRecord(
            alarm_id="alm-001",
            alarm_type="CPU_HIGH",
            severity=AlarmSeverity.MAJOR,
            state=AlarmState.ACTIVE,
            timestamp=datetime(2026, 8, 11, 18, 0),
            source=NodeInstanceId("streaming-primary"),
            title="CPU high",
            description="CPU exceeded threshold.",
        )


def test_acknowledged_alarm_requires_operator() -> None:
    with pytest.raises(ValueError):
        make_alarm(
            state=AlarmState.ACKNOWLEDGED,
            acknowledged=True,
            acknowledged_at=now(),
        )


def test_acknowledged_alarm_requires_timestamp() -> None:
    with pytest.raises(ValueError):
        make_alarm(
            state=AlarmState.ACKNOWLEDGED,
            acknowledged=True,
            acknowledged_by="operator-01",
        )


def test_acknowledged_state_requires_acknowledged_true() -> None:
    with pytest.raises(ValueError):
        make_alarm(
            state=AlarmState.ACKNOWLEDGED,
        )


def test_valid_acknowledged_alarm() -> None:
    alarm = make_alarm(
        state=AlarmState.ACKNOWLEDGED,
        acknowledged=True,
        acknowledged_by="operator-01",
        acknowledged_at=now(),
    )

    assert alarm.is_acknowledged is True
    assert alarm.requires_attention is True


def test_resolved_state_requires_resolved_at() -> None:
    with pytest.raises(ValueError):
        make_alarm(
            state=AlarmState.RESOLVED,
        )


def test_valid_resolved_alarm() -> None:
    raised = now()
    resolved = raised + timedelta(minutes=5)

    alarm = AlarmRecord(
        alarm_id="alm-001",
        alarm_type="CPU_HIGH",
        severity=AlarmSeverity.MAJOR,
        state=AlarmState.RESOLVED,
        timestamp=raised,
        source=NodeInstanceId("streaming-primary"),
        title="CPU high",
        description="CPU exceeded threshold.",
        resolved_at=resolved,
    )

    assert alarm.is_resolved is True
    assert alarm.requires_attention is False


def test_closed_state_requires_resolved_and_closed_times() -> None:
    with pytest.raises(ValueError):
        make_alarm(
            state=AlarmState.CLOSED,
        )


def test_valid_closed_alarm() -> None:
    raised = now()
    resolved = raised + timedelta(minutes=5)
    closed = resolved + timedelta(minutes=2)

    alarm = AlarmRecord(
        alarm_id="alm-001",
        alarm_type="CPU_HIGH",
        severity=AlarmSeverity.MAJOR,
        state=AlarmState.CLOSED,
        timestamp=raised,
        source=NodeInstanceId("streaming-primary"),
        title="CPU high",
        description="CPU exceeded threshold.",
        resolved_at=resolved,
        closed_at=closed,
    )

    assert alarm.is_closed is True
    assert alarm.requires_attention is False


def test_resolved_at_cannot_precede_timestamp() -> None:
    raised = now()

    with pytest.raises(ValueError):
        AlarmRecord(
            alarm_id="alm-001",
            alarm_type="CPU_HIGH",
            severity=AlarmSeverity.MAJOR,
            state=AlarmState.RESOLVED,
            timestamp=raised,
            source=NodeInstanceId("streaming-primary"),
            title="CPU high",
            description="CPU exceeded threshold.",
            resolved_at=raised - timedelta(seconds=1),
        )


def test_closed_at_cannot_precede_resolved_at() -> None:
    raised = now()
    resolved = raised + timedelta(minutes=5)

    with pytest.raises(ValueError):
        AlarmRecord(
            alarm_id="alm-001",
            alarm_type="CPU_HIGH",
            severity=AlarmSeverity.MAJOR,
            state=AlarmState.CLOSED,
            timestamp=raised,
            source=NodeInstanceId("streaming-primary"),
            title="CPU high",
            description="CPU exceeded threshold.",
            resolved_at=resolved,
            closed_at=resolved - timedelta(seconds=1),
        )


def test_alarm_attributes_are_immutable() -> None:
    alarm = make_alarm()

    with pytest.raises(TypeError):
        alarm.attributes["threshold"] = "90"  # type: ignore[index]


def test_alarm_record_is_immutable() -> None:
    alarm = make_alarm()

    with pytest.raises(AttributeError):
        alarm.state = AlarmState.CLOSED  # type: ignore[misc]


def test_alarm_string_representation() -> None:
    alarm = make_alarm()

    assert str(alarm) == (
        "CPU_HIGH: CPU usage exceeded threshold"
    )


def test_node_alarm_can_be_empty() -> None:
    alarms = NodeAlarm()

    assert alarms.alarms == ()
    assert len(alarms) == 0


def test_node_alarm_accepts_multiple_alarms() -> None:
    alarms = NodeAlarm(
        alarms=(
            make_alarm(alarm_id="alm-001"),
            make_alarm(
                alarm_id="alm-002",
                alarm_type="NETWORK_LOST",
            ),
        )
    )

    assert len(alarms) == 2


def test_node_alarm_rejects_duplicate_ids() -> None:
    with pytest.raises(ValueError):
        NodeAlarm(
            alarms=(
                make_alarm(alarm_id="alm-001"),
                make_alarm(alarm_id="alm-001"),
            )
        )


def test_node_alarm_get_alarm() -> None:
    alarm = make_alarm()

    alarms = NodeAlarm(
        alarms=(alarm,)
    )

    assert alarms.get("alm-001") is alarm


def test_node_alarm_active_collection() -> None:
    raised = now()

    alarms = NodeAlarm(
        alarms=(
            make_alarm(
                alarm_id="alm-001",
                state=AlarmState.ACTIVE,
            ),
            AlarmRecord(
                alarm_id="alm-002",
                alarm_type="NETWORK_LOST",
                severity=AlarmSeverity.CRITICAL,
                state=AlarmState.RESOLVED,
                timestamp=raised,
                source=NodeInstanceId("streaming-primary"),
                title="Network lost",
                description="Network connection was lost.",
                resolved_at=raised + timedelta(minutes=1),
            ),
        )
    )

    assert len(alarms.active) == 1
    assert alarms.active[0].alarm_id == "alm-001"


def test_node_alarm_by_severity() -> None:
    alarms = NodeAlarm(
        alarms=(
            make_alarm(
                alarm_id="alm-001",
                severity=AlarmSeverity.MAJOR,
            ),
            make_alarm(
                alarm_id="alm-002",
                severity=AlarmSeverity.CRITICAL,
            ),
        )
    )

    result = alarms.by_severity(
        AlarmSeverity.CRITICAL
    )

    assert len(result) == 1
    assert result[0].alarm_id == "alm-002"


def test_node_alarm_by_type() -> None:
    alarms = NodeAlarm(
        alarms=(
            make_alarm(
                alarm_id="alm-001",
                alarm_type="CPU_HIGH",
            ),
            make_alarm(
                alarm_id="alm-002",
                alarm_type="CPU_HIGH",
            ),
            make_alarm(
                alarm_id="alm-003",
                alarm_type="NETWORK_LOST",
            ),
        )
    )

    assert len(
        alarms.by_type("cpu_high")
    ) == 2


def test_node_alarm_rejects_non_tuple() -> None:
    with pytest.raises(TypeError):
        NodeAlarm(
            alarms=[]  # type: ignore[arg-type]
        )


def test_node_alarm_rejects_invalid_entry() -> None:
    with pytest.raises(TypeError):
        NodeAlarm(
            alarms=(
                "CPU_HIGH",  # type: ignore[arg-type]
            )
        )
