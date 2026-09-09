"""Tests for Stream Health alarm policy.

ENG-013B — Stream Health Contract Block 5

The initial production policy is intentionally conservative.

Health describes operational condition.  It does not, by itself,
authorize operator-facing alarm creation.  Rich decisions based on
role, scope, impact, expected presence and affected population belong
to later contract blocks.

These tests therefore protect the policy boundary without inventing
operational semantics that Stream Health does not yet carry.
"""

from datetime import UTC, datetime

import pytest

from app.domain.streaming.health import (
    HealthStatus,
    StreamingHealth,
)
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.streaming_health_alarm_policy import (
    StreamingHealthAlarmAction,
    StreamingHealthAlarmDecision,
    StreamingHealthAlarmPolicy,
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


def health(status: HealthStatus) -> StreamingHealth:
    return StreamingHealth(
        captured_at=TIMESTAMP,
        paths=(),
        status=status,
        message=f"stream health is {status.value}",
    )


def transition(
    previous: HealthStatus,
    current: HealthStatus,
    kind: HealthTransitionKind,
) -> StreamingHealthTransition:
    return StreamingHealthTransition(
        previous=health(previous),
        current=health(current),
        kind=kind,
    )


@pytest.mark.parametrize(
    (
        "previous",
        "current",
        "kind",
    ),
    (
        (
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthTransitionKind.DEGRADED,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
        ),
        (
            HealthStatus.DEGRADED,
            HealthStatus.CRITICAL,
            HealthTransitionKind.DEGRADED,
        ),
        (
            HealthStatus.HEALTHY,
            HealthStatus.UNKNOWN,
            HealthTransitionKind.UNKNOWN,
        ),
        (
            HealthStatus.UNKNOWN,
            HealthStatus.CRITICAL,
            HealthTransitionKind.UNKNOWN,
        ),
    ),
)
def test_health_severity_alone_does_not_raise_alarm(
    previous,
    current,
    kind,
):
    policy = StreamingHealthAlarmPolicy()

    decision = policy.evaluate(
        transition=transition(
            previous,
            current,
            kind,
        )
    )

    assert isinstance(
        decision,
        StreamingHealthAlarmDecision,
    )
    assert decision.action is StreamingHealthAlarmAction.NONE
    assert decision.transition is not None


def test_none_transition_requires_no_alarm_action():
    policy = StreamingHealthAlarmPolicy()

    decision = policy.evaluate(
        transition=None
    )

    assert decision.action is StreamingHealthAlarmAction.NONE
    assert decision.transition is None


@pytest.mark.parametrize(
    (
        "previous",
        "kind",
    ),
    (
        (
            HealthStatus.DEGRADED,
            HealthTransitionKind.RECOVERED,
        ),
        (
            HealthStatus.CRITICAL,
            HealthTransitionKind.RECOVERED,
        ),
    ),
)
def test_recovery_requests_resolution_of_existing_alarm(
    previous,
    kind,
):
    policy = StreamingHealthAlarmPolicy()

    value = transition(
        previous,
        HealthStatus.HEALTHY,
        kind,
    )

    decision = policy.evaluate(
        transition=value
    )

    assert decision.action is StreamingHealthAlarmAction.RESOLVE
    assert decision.transition is value


def test_partial_improvement_keeps_existing_alarm():
    policy = StreamingHealthAlarmPolicy()

    value = transition(
        HealthStatus.CRITICAL,
        HealthStatus.DEGRADED,
        HealthTransitionKind.IMPROVED,
    )

    decision = policy.evaluate(
        transition=value
    )

    assert decision.action is StreamingHealthAlarmAction.KEEP
    assert decision.transition is value


def test_unknown_does_not_resolve_existing_alarm():
    policy = StreamingHealthAlarmPolicy()

    value = transition(
        HealthStatus.CRITICAL,
        HealthStatus.UNKNOWN,
        HealthTransitionKind.UNKNOWN,
    )

    decision = policy.evaluate(
        transition=value
    )

    assert decision.action is StreamingHealthAlarmAction.KEEP
    assert decision.transition is value


def test_decision_is_immutable():
    policy = StreamingHealthAlarmPolicy()

    decision = policy.evaluate(
        transition=None
    )

    with pytest.raises(
        AttributeError,
    ):
        decision.action = StreamingHealthAlarmAction.KEEP


def test_policy_rejects_invalid_transition():
    policy = StreamingHealthAlarmPolicy()

    with pytest.raises(
        TypeError,
        match=(
            "transition must be a "
            "StreamingHealthTransition or None"
        ),
    ):
        policy.evaluate(
            transition=object(),  # type: ignore[arg-type]
        )
