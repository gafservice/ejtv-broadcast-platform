"""Tests for Stream Health alarm creation.

ENG-013B — Stream Health Contract Block 5

The factory materializes an AlarmRecord only after alarm policy has
explicitly authorized a RAISE action.

It does not evaluate health, detect transitions, decide policy,
persist alarms or manage alarm lifecycle.
"""

from datetime import UTC, datetime

import pytest

from app.domain.streaming.health import (
    HealthStatus,
    StreamingHealth,
)
from app.noc.domain.node_alarm import (
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.streaming_health_alarm_policy import (
    StreamingHealthAlarmAction,
    StreamingHealthAlarmDecision,
)
from app.services.streaming_health_transition_alarm_factory import (
    StreamingHealthTransitionAlarmFactory,
)
from app.services.streaming_health_transition_detector import (
    StreamingHealthTransition,
)


TIMESTAMP = datetime(
    2026,
    9,
    8,
    12,
    0,
    tzinfo=UTC,
)

SOURCE = NodeInstanceId("streaming-primary")


def health(status: HealthStatus) -> StreamingHealth:
    return StreamingHealth(
        captured_at=TIMESTAMP,
        paths=(),
        status=status,
        message=f"stream health is {status.value}",
    )


def critical_transition() -> StreamingHealthTransition:
    return StreamingHealthTransition(
        previous=health(HealthStatus.HEALTHY),
        current=health(HealthStatus.CRITICAL),
        kind=HealthTransitionKind.DEGRADED,
    )


def raise_decision() -> StreamingHealthAlarmDecision:
    return StreamingHealthAlarmDecision(
        action=StreamingHealthAlarmAction.RAISE,
        transition=critical_transition(),
    )


def test_factory_creates_alarm_only_for_raise_decision():
    factory = StreamingHealthTransitionAlarmFactory()

    alarm = factory.create(
        decision=raise_decision(),
        source=SOURCE,
        timestamp=TIMESTAMP,
    )

    assert alarm is not None
    assert alarm.alarm_type == "STREAM_HEALTH"
    assert alarm.severity is AlarmSeverity.CRITICAL
    assert alarm.state is AlarmState.ACTIVE
    assert alarm.source == SOURCE


def test_alarm_contains_stream_health_transition_context():
    factory = StreamingHealthTransitionAlarmFactory()

    alarm = factory.create(
        decision=raise_decision(),
        source=SOURCE,
        timestamp=TIMESTAMP,
    )

    assert alarm is not None
    assert alarm.attributes is not None
    assert alarm.attributes["previous"] == "HEALTHY"
    assert alarm.attributes["current"] == "CRITICAL"
    assert alarm.attributes["transition"] == (
        HealthTransitionKind.DEGRADED.value
    )


@pytest.mark.parametrize(
    "action",
    (
        StreamingHealthAlarmAction.NONE,
        StreamingHealthAlarmAction.KEEP,
        StreamingHealthAlarmAction.RESOLVE,
    ),
)
def test_factory_returns_none_when_raise_not_authorized(
    action,
):
    factory = StreamingHealthTransitionAlarmFactory()

    decision = StreamingHealthAlarmDecision(
        action=action,
        transition=critical_transition(),
    )

    alarm = factory.create(
        decision=decision,
        source=SOURCE,
        timestamp=TIMESTAMP,
    )

    assert alarm is None


def test_factory_requires_transition_for_raise():
    factory = StreamingHealthTransitionAlarmFactory()

    decision = StreamingHealthAlarmDecision(
        action=StreamingHealthAlarmAction.RAISE,
        transition=None,
    )

    with pytest.raises(
        ValueError,
        match="RAISE decision requires a transition",
    ):
        factory.create(
            decision=decision,
            source=SOURCE,
            timestamp=TIMESTAMP,
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "value",
        "expected_message",
    ),
    (
        (
            "decision",
            object(),
            "decision must be a StreamingHealthAlarmDecision",
        ),
        (
            "source",
            "streaming-primary",
            "source must be a NodeInstanceId",
        ),
        (
            "timestamp",
            "invalid",
            "timestamp must be a datetime",
        ),
    ),
)
def test_factory_rejects_invalid_arguments(
    field_name,
    value,
    expected_message,
):
    factory = StreamingHealthTransitionAlarmFactory()

    arguments = {
        "decision": raise_decision(),
        "source": SOURCE,
        "timestamp": TIMESTAMP,
    }

    arguments[field_name] = value

    with pytest.raises(
        TypeError,
        match=expected_message,
    ):
        factory.create(**arguments)
