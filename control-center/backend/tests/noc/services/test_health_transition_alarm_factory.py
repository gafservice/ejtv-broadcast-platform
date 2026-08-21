"""Tests for NodeHealth transition operational alarm creation."""

from datetime import UTC, datetime, timedelta

import pytest

from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.health_transition_alarm_factory import (
    HealthTransitionAlarmFactory,
)
from app.noc.services.health_transition_detector import (
    HealthTransition,
    HealthTransitionKind,
)


BASE_TIME = datetime(
    2026,
    8,
    21,
    22,
    30,
    tzinfo=UTC,
)


def make_transition(
    *,
    previous: NodeHealthState,
    current: NodeHealthState,
    kind: HealthTransitionKind,
) -> HealthTransition:
    return HealthTransition(
        previous=NodeHealth(previous),
        current=NodeHealth(current),
        kind=kind,
    )


def test_factory_requires_transition() -> None:
    factory = HealthTransitionAlarmFactory()

    with pytest.raises(TypeError):
        factory.create(
            transition=object(),  # type: ignore[arg-type]
            source=NodeInstanceId("streaming-primary"),
            timestamp=BASE_TIME,
        )


def test_factory_requires_source() -> None:
    factory = HealthTransitionAlarmFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    with pytest.raises(TypeError):
        factory.create(
            transition=transition,
            source="streaming-primary",  # type: ignore[arg-type]
            timestamp=BASE_TIME,
        )


def test_factory_requires_datetime() -> None:
    factory = HealthTransitionAlarmFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    with pytest.raises(TypeError):
        factory.create(
            transition=transition,
            source=NodeInstanceId("streaming-primary"),
            timestamp="2026-08-21T22:30:00Z",  # type: ignore[arg-type]
        )


def test_factory_requires_timezone_aware_timestamp() -> None:
    factory = HealthTransitionAlarmFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    naive = datetime(
        2026,
        8,
        21,
        22,
        30,
    )

    with pytest.raises(ValueError):
        factory.create(
            transition=transition,
            source=NodeInstanceId("streaming-primary"),
            timestamp=naive,
        )


def test_factory_requires_utc_timestamp() -> None:
    factory = HealthTransitionAlarmFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    non_utc = datetime(
        2026,
        8,
        21,
        16,
        30,
        tzinfo=__import__("datetime").timezone(
            -timedelta(hours=6)
        ),
    )

    with pytest.raises(ValueError):
        factory.create(
            transition=transition,
            source=NodeInstanceId("streaming-primary"),
            timestamp=non_utc,
        )


def test_warning_degradation_creates_warning_alarm() -> None:
    factory = HealthTransitionAlarmFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    alarm = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert isinstance(alarm, AlarmRecord)
    assert alarm.alarm_type == "NODE_HEALTH_DEGRADED"
    assert alarm.severity is AlarmSeverity.WARNING
    assert alarm.state is AlarmState.ACTIVE
    assert alarm.source == NodeInstanceId("streaming-primary")
    assert alarm.timestamp == BASE_TIME


def test_degraded_state_creates_major_alarm() -> None:
    factory = HealthTransitionAlarmFactory()

    transition = make_transition(
        previous=NodeHealthState.WARNING,
        current=NodeHealthState.DEGRADED,
        kind=HealthTransitionKind.DEGRADED,
    )

    alarm = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert alarm is not None
    assert alarm.severity is AlarmSeverity.MAJOR


def test_critical_state_creates_critical_alarm() -> None:
    factory = HealthTransitionAlarmFactory()

    transition = make_transition(
        previous=NodeHealthState.DEGRADED,
        current=NodeHealthState.CRITICAL,
        kind=HealthTransitionKind.DEGRADED,
    )

    alarm = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert alarm is not None
    assert alarm.severity is AlarmSeverity.CRITICAL


@pytest.mark.parametrize(
    (
        "previous",
        "current",
        "kind",
    ),
    (
        (
            NodeHealthState.CRITICAL,
            NodeHealthState.DEGRADED,
            HealthTransitionKind.IMPROVED,
        ),
        (
            NodeHealthState.WARNING,
            NodeHealthState.HEALTHY,
            HealthTransitionKind.RECOVERED,
        ),
        (
            NodeHealthState.HEALTHY,
            NodeHealthState.UNKNOWN,
            HealthTransitionKind.UNKNOWN,
        ),
    ),
)
def test_non_alarm_transition_returns_none(
    previous: NodeHealthState,
    current: NodeHealthState,
    kind: HealthTransitionKind,
) -> None:
    factory = HealthTransitionAlarmFactory()

    transition = make_transition(
        previous=previous,
        current=current,
        kind=kind,
    )

    assert (
        factory.create(
            transition=transition,
            source=NodeInstanceId("streaming-primary"),
            timestamp=BASE_TIME,
        )
        is None
    )


def test_alarm_contains_transition_attributes() -> None:
    factory = HealthTransitionAlarmFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.CRITICAL,
        kind=HealthTransitionKind.DEGRADED,
    )

    alarm = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert alarm is not None
    assert alarm.attributes is not None
    assert alarm.attributes["previous"] == "HEALTHY"
    assert alarm.attributes["current"] == "CRITICAL"
    assert alarm.attributes["transition"] == "DEGRADED"


def test_alarm_title_contains_current_state() -> None:
    factory = HealthTransitionAlarmFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.CRITICAL,
        kind=HealthTransitionKind.DEGRADED,
    )

    alarm = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert alarm is not None
    assert "CRITICAL" in alarm.title


def test_alarm_description_contains_previous_and_current_state() -> None:
    factory = HealthTransitionAlarmFactory()

    transition = make_transition(
        previous=NodeHealthState.WARNING,
        current=NodeHealthState.DEGRADED,
        kind=HealthTransitionKind.DEGRADED,
    )

    alarm = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert alarm is not None
    assert "WARNING" in alarm.description
    assert "DEGRADED" in alarm.description


def test_alarm_id_is_not_empty() -> None:
    factory = HealthTransitionAlarmFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    alarm = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert alarm is not None
    assert isinstance(alarm.alarm_id, str)
    assert alarm.alarm_id.strip()


def test_alarm_id_is_unique_per_creation() -> None:
    factory = HealthTransitionAlarmFactory()

    transition = make_transition(
        previous=NodeHealthState.HEALTHY,
        current=NodeHealthState.WARNING,
        kind=HealthTransitionKind.DEGRADED,
    )

    first = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    second = factory.create(
        transition=transition,
        source=NodeInstanceId("streaming-primary"),
        timestamp=BASE_TIME,
    )

    assert first is not None
    assert second is not None
    assert first.alarm_id != second.alarm_id
