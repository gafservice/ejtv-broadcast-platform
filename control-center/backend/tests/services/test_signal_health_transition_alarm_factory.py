"""Contract tests for Signal Health alarm materialization.

ENG-013C — Block 232C.2

The factory converts an already-authorized SignalHealthAlarmDecision into
an AlarmRecord only when the decision explicitly authorizes RAISE.

It must not:

- evaluate Signal Health;
- evaluate Media Health;
- evaluate Source Transport Health;
- detect transitions;
- decide alarm policy;
- persist alarms;
- manage alarm lifecycle.
"""

from datetime import UTC, datetime

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.signal_health import SignalHealth
from app.noc.domain.node_alarm import (
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.signal_health_alarm_policy import (
    SignalHealthAlarmAction,
    SignalHealthAlarmDecision,
)
from app.services.signal_health_transition_alarm_factory import (
    SignalHealthTransitionAlarmFactory,
)
from app.services.signal_health_transition_detector import (
    SignalHealthTransition,
)


TIMESTAMP = datetime(
    2026,
    9,
    25,
    18,
    0,
    tzinfo=UTC,
)

SOURCE = NodeInstanceId("streaming-primary")

PROFILE_ID = "impact"
SERVICE_ID = "impact"
PATH_NAME = "impact"


def health(
    status: HealthStatus,
    *,
    media_status: HealthStatus = HealthStatus.HEALTHY,
    transport_status: HealthStatus = HealthStatus.HEALTHY,
    path_name: str | None = PATH_NAME,
) -> SignalHealth:
    return SignalHealth(
        profile_id=PROFILE_ID,
        service_id=SERVICE_ID,
        path_name=path_name,
        media_status=media_status,
        transport_status=transport_status,
        status=status,
    )


def degraded_transition() -> SignalHealthTransition:
    return SignalHealthTransition(
        previous=health(
            HealthStatus.HEALTHY,
        ),
        current=health(
            HealthStatus.DEGRADED,
            media_status=HealthStatus.DEGRADED,
        ),
        kind=HealthTransitionKind.DEGRADED,
    )


def critical_transition() -> SignalHealthTransition:
    return SignalHealthTransition(
        previous=health(
            HealthStatus.HEALTHY,
        ),
        current=health(
            HealthStatus.CRITICAL,
            media_status=HealthStatus.CRITICAL,
        ),
        kind=HealthTransitionKind.DEGRADED,
    )


def raise_decision(
    transition: SignalHealthTransition | None = None,
) -> SignalHealthAlarmDecision:
    return SignalHealthAlarmDecision(
        action=SignalHealthAlarmAction.RAISE,
        transition=(
            transition
            if transition is not None
            else critical_transition()
        ),
    )


@pytest.mark.parametrize(
    (
        "transition",
        "expected_severity",
    ),
    (
        (
            degraded_transition(),
            AlarmSeverity.MAJOR,
        ),
        (
            critical_transition(),
            AlarmSeverity.CRITICAL,
        ),
    ),
)
def test_factory_creates_active_signal_health_alarm(
    transition,
    expected_severity,
):
    factory = SignalHealthTransitionAlarmFactory()

    alarm = factory.create(
        decision=raise_decision(transition),
        source=SOURCE,
        timestamp=TIMESTAMP,
    )

    assert alarm is not None
    assert alarm.alarm_id.startswith("alm-")
    assert alarm.alarm_type == "SIGNAL_HEALTH"
    assert alarm.severity is expected_severity
    assert alarm.state is AlarmState.ACTIVE
    assert alarm.timestamp == TIMESTAMP
    assert alarm.source == SOURCE


def test_alarm_contains_complete_signal_health_context():
    factory = SignalHealthTransitionAlarmFactory()

    value = critical_transition()

    alarm = factory.create(
        decision=raise_decision(value),
        source=SOURCE,
        timestamp=TIMESTAMP,
    )

    assert alarm is not None
    assert alarm.attributes is not None

    assert alarm.attributes["profile_id"] == PROFILE_ID
    assert alarm.attributes["service_id"] == SERVICE_ID
    assert alarm.attributes["path_name"] == PATH_NAME

    assert alarm.attributes["previous"] == "HEALTHY"
    assert alarm.attributes["current"] == "CRITICAL"
    assert alarm.attributes["transition"] == (
        HealthTransitionKind.DEGRADED.value
    )

    assert alarm.attributes["media_previous"] == "HEALTHY"
    assert alarm.attributes["media_current"] == "CRITICAL"

    assert alarm.attributes["transport_previous"] == "HEALTHY"
    assert alarm.attributes["transport_current"] == "HEALTHY"


def test_factory_omits_path_name_when_signal_path_is_none():
    factory = SignalHealthTransitionAlarmFactory()

    value = SignalHealthTransition(
        previous=health(
            HealthStatus.HEALTHY,
            path_name=None,
        ),
        current=health(
            HealthStatus.DEGRADED,
            media_status=HealthStatus.DEGRADED,
            path_name=None,
        ),
        kind=HealthTransitionKind.DEGRADED,
    )

    alarm = factory.create(
        decision=raise_decision(value),
        source=SOURCE,
        timestamp=TIMESTAMP,
    )

    assert alarm is not None
    assert alarm.attributes is not None
    assert "path_name" not in alarm.attributes


@pytest.mark.parametrize(
    "action",
    (
        SignalHealthAlarmAction.NONE,
        SignalHealthAlarmAction.KEEP,
        SignalHealthAlarmAction.RESOLVE,
    ),
)
def test_factory_returns_none_when_raise_not_authorized(
    action,
):
    factory = SignalHealthTransitionAlarmFactory()

    decision = SignalHealthAlarmDecision(
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
    factory = SignalHealthTransitionAlarmFactory()

    decision = SignalHealthAlarmDecision(
        action=SignalHealthAlarmAction.RAISE,
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
            "decision must be a SignalHealthAlarmDecision",
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
    factory = SignalHealthTransitionAlarmFactory()

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


def test_factory_rejects_naive_timestamp():
    factory = SignalHealthTransitionAlarmFactory()

    with pytest.raises(
        ValueError,
        match="timestamp must be timezone-aware and UTC",
    ):
        factory.create(
            decision=raise_decision(),
            source=SOURCE,
            timestamp=datetime(
                2026,
                9,
                25,
                18,
                0,
            ),
        )


def test_factory_rejects_non_utc_timestamp():
    factory = SignalHealthTransitionAlarmFactory()

    from datetime import timedelta, timezone

    non_utc = datetime(
        2026,
        9,
        25,
        18,
        0,
        tzinfo=timezone(timedelta(hours=-6)),
    )

    with pytest.raises(
        ValueError,
        match="timestamp must be expressed in UTC",
    ):
        factory.create(
            decision=raise_decision(),
            source=SOURCE,
            timestamp=non_utc,
        )
