"""Contract tests for Signal Health alarm policy.

ENG-013C — Block 232C

The policy consumes one already-detected SignalHealthTransition and decides
only the alarm lifecycle action.

It must not:

- evaluate Signal Health;
- evaluate Media Health;
- evaluate Source Transport Health;
- detect or reclassify transitions;
- create alarms;
- persist alarms;
- inspect whether an alarm currently exists;
- interact with AlarmService.
"""

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.signal_health import SignalHealth
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.signal_health_alarm_policy import (
    SignalHealthAlarmAction,
    SignalHealthAlarmDecision,
    SignalHealthAlarmPolicy,
)
from app.services.signal_health_transition_detector import (
    SignalHealthTransition,
)


PROFILE_ID = "impact"
SERVICE_ID = "impact"
PATH_NAME = "impact"


def health(status: HealthStatus) -> SignalHealth:
    return SignalHealth(
        profile_id=PROFILE_ID,
        service_id=SERVICE_ID,
        path_name=PATH_NAME,
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.HEALTHY,
        status=status,
    )


def transition(
    previous: HealthStatus,
    current: HealthStatus,
    kind: HealthTransitionKind,
) -> SignalHealthTransition:
    return SignalHealthTransition(
        previous=health(previous),
        current=health(current),
        kind=kind,
    )


@pytest.mark.parametrize(
    (
        "previous",
        "current",
        "kind",
        "expected_action",
    ),
    (
        (
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthTransitionKind.DEGRADED,
            SignalHealthAlarmAction.RAISE,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
            SignalHealthAlarmAction.RAISE,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
            SignalHealthAlarmAction.KEEP,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.DEGRADED,
            HealthTransitionKind.IMPROVED,
            SignalHealthAlarmAction.KEEP,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.HEALTHY,
            HealthTransitionKind.RECOVERED,
            SignalHealthAlarmAction.RESOLVE,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.HEALTHY,
            HealthTransitionKind.RECOVERED,
            SignalHealthAlarmAction.RESOLVE,
        ),
        (
            HealthStatus.CRITICAL,
            HealthStatus.UNKNOWN,
            HealthTransitionKind.UNKNOWN,
            SignalHealthAlarmAction.KEEP,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.UNKNOWN,
            HealthTransitionKind.UNKNOWN,
            SignalHealthAlarmAction.KEEP,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.HEALTHY,
            HealthTransitionKind.UNKNOWN,
            SignalHealthAlarmAction.RESOLVE,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.DEGRADED,
            HealthTransitionKind.UNKNOWN,
            SignalHealthAlarmAction.KEEP,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.CRITICAL,
            HealthTransitionKind.UNKNOWN,
            SignalHealthAlarmAction.KEEP,
        ),
    ),
)
def test_policy_maps_signal_transition_to_alarm_action(
    previous,
    current,
    kind,
    expected_action,
):
    policy = SignalHealthAlarmPolicy()

    value = transition(
        previous,
        current,
        kind,
    )

    decision = policy.evaluate(
        transition=value,
    )

    assert isinstance(
        decision,
        SignalHealthAlarmDecision,
    )
    assert decision.action is expected_action
    assert decision.transition is value


def test_none_transition_produces_none_action():
    policy = SignalHealthAlarmPolicy()

    decision = policy.evaluate(
        transition=None,
    )

    assert isinstance(
        decision,
        SignalHealthAlarmDecision,
    )
    assert decision.action is SignalHealthAlarmAction.NONE
    assert decision.transition is None


def test_unknown_to_healthy_keeps_transition_kind_but_resolves_alarm_lifecycle():
    policy = SignalHealthAlarmPolicy()

    value = transition(
        HealthStatus.UNKNOWN,
        HealthStatus.HEALTHY,
        HealthTransitionKind.UNKNOWN,
    )

    assert value.kind is HealthTransitionKind.UNKNOWN

    decision = policy.evaluate(
        transition=value,
    )

    assert value.kind is HealthTransitionKind.UNKNOWN
    assert decision.transition is value
    assert decision.action is SignalHealthAlarmAction.RESOLVE
    assert decision.transition is value
    assert decision.transition.kind is HealthTransitionKind.UNKNOWN


def test_policy_rejects_invalid_transition():
    policy = SignalHealthAlarmPolicy()

    with pytest.raises(
        TypeError,
        match=(
            "transition must be a "
            "SignalHealthTransition or None"
        ),
    ):
        policy.evaluate(
            transition=object(),
        )
