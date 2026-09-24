"""Contract tests for Media Health current-state freshness.

ENG-013C — Signal Health

Freshness is a consumer-side temporal policy.

The current-state repository stores the latest known stabilized
MediaHealth projection. It does not decide whether that projection
is still recent enough for a Signal Health decision.

A stale MediaHealth projection represents insufficient current
evidence. Staleness is not itself DEGRADED or CRITICAL.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import MediaHealth
from app.noc.current_state.media_health_current_state import (
    MediaHealthCurrentState,
)
from app.noc.current_state.media_health_freshness import (
    MediaHealthFreshnessPolicy,
)


def _state(
    *,
    observed_at: datetime,
    status: HealthStatus = HealthStatus.HEALTHY,
) -> MediaHealthCurrentState:
    health = MediaHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        status=status,
    )

    return MediaHealthCurrentState(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        observed_at=observed_at,
        health=health,
    )


def test_recent_state_is_fresh() -> None:
    now = datetime(
        2026, 9, 24, 3, 0, 0,
        tzinfo=timezone.utc,
    )

    policy = MediaHealthFreshnessPolicy(
        max_age_seconds=16.0,
    )

    state = _state(
        observed_at=now - timedelta(seconds=8),
    )

    assert policy.is_fresh(
        state=state,
        now=now,
    ) is True


def test_state_exactly_at_max_age_is_fresh() -> None:
    now = datetime(
        2026, 9, 24, 3, 0, 0,
        tzinfo=timezone.utc,
    )

    policy = MediaHealthFreshnessPolicy(
        max_age_seconds=16.0,
    )

    state = _state(
        observed_at=now - timedelta(seconds=16),
    )

    assert policy.is_fresh(
        state=state,
        now=now,
    ) is True


def test_state_older_than_max_age_is_stale() -> None:
    now = datetime(
        2026, 9, 24, 3, 0, 0,
        tzinfo=timezone.utc,
    )

    policy = MediaHealthFreshnessPolicy(
        max_age_seconds=16.0,
    )

    state = _state(
        observed_at=(
            now
            - timedelta(seconds=16, microseconds=1)
        ),
    )

    assert policy.is_fresh(
        state=state,
        now=now,
    ) is False


def test_zero_max_age_accepts_same_instant() -> None:
    now = datetime(
        2026, 9, 24, 3, 0, 0,
        tzinfo=timezone.utc,
    )

    policy = MediaHealthFreshnessPolicy(
        max_age_seconds=0.0,
    )

    state = _state(observed_at=now)

    assert policy.is_fresh(
        state=state,
        now=now,
    ) is True


def test_zero_max_age_rejects_older_state() -> None:
    now = datetime(
        2026, 9, 24, 3, 0, 0,
        tzinfo=timezone.utc,
    )

    policy = MediaHealthFreshnessPolicy(
        max_age_seconds=0.0,
    )

    state = _state(
        observed_at=now - timedelta(microseconds=1),
    )

    assert policy.is_fresh(
        state=state,
        now=now,
    ) is False


@pytest.mark.parametrize(
    "max_age_seconds",
    [-1.0, -0.001],
)
def test_negative_max_age_is_rejected(
    max_age_seconds: float,
) -> None:
    with pytest.raises(ValueError):
        MediaHealthFreshnessPolicy(
            max_age_seconds=max_age_seconds,
        )


@pytest.mark.parametrize(
    "max_age_seconds",
    [float("nan"), float("inf"), float("-inf")],
)
def test_non_finite_max_age_is_rejected(
    max_age_seconds: float,
) -> None:
    with pytest.raises(ValueError):
        MediaHealthFreshnessPolicy(
            max_age_seconds=max_age_seconds,
        )


def test_wrong_state_type_is_rejected() -> None:
    now = datetime(
        2026, 9, 24, 3, 0, 0,
        tzinfo=timezone.utc,
    )

    policy = MediaHealthFreshnessPolicy(
        max_age_seconds=16.0,
    )

    with pytest.raises(TypeError):
        policy.is_fresh(
            state=object(),
            now=now,
        )


def test_naive_now_is_rejected() -> None:
    observed_at = datetime(
        2026, 9, 24, 3, 0, 0,
        tzinfo=timezone.utc,
    )

    policy = MediaHealthFreshnessPolicy(
        max_age_seconds=16.0,
    )

    state = _state(
        observed_at=observed_at,
    )

    with pytest.raises(ValueError):
        policy.is_fresh(
            state=state,
            now=datetime(2026, 9, 24, 3, 0, 0),
        )


def test_wrong_now_type_is_rejected() -> None:
    observed_at = datetime(
        2026, 9, 24, 3, 0, 0,
        tzinfo=timezone.utc,
    )

    policy = MediaHealthFreshnessPolicy(
        max_age_seconds=16.0,
    )

    state = _state(
        observed_at=observed_at,
    )

    with pytest.raises(TypeError):
        policy.is_fresh(
            state=state,
            now="2026-09-24T03:00:00+00:00",
        )


def test_future_observation_is_rejected() -> None:
    now = datetime(
        2026, 9, 24, 3, 0, 0,
        tzinfo=timezone.utc,
    )

    policy = MediaHealthFreshnessPolicy(
        max_age_seconds=16.0,
    )

    state = _state(
        observed_at=now + timedelta(microseconds=1),
    )

    with pytest.raises(ValueError):
        policy.is_fresh(
            state=state,
            now=now,
        )


def test_freshness_does_not_depend_on_health_status() -> None:
    now = datetime(
        2026, 9, 24, 3, 0, 0,
        tzinfo=timezone.utc,
    )

    policy = MediaHealthFreshnessPolicy(
        max_age_seconds=16.0,
    )

    for status in HealthStatus:
        state = _state(
            observed_at=now - timedelta(seconds=8),
            status=status,
        )

        assert policy.is_fresh(
            state=state,
            now=now,
        ) is True


def test_policy_does_not_mutate_current_state() -> None:
    now = datetime(
        2026, 9, 24, 3, 0, 0,
        tzinfo=timezone.utc,
    )

    state = _state(
        observed_at=now - timedelta(seconds=8),
    )

    before = state

    policy = MediaHealthFreshnessPolicy(
        max_age_seconds=16.0,
    )

    policy.is_fresh(
        state=state,
        now=now,
    )

    assert state == before
