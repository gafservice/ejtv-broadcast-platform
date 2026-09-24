"""Contract for effective Media Health current-state resolution.

ENG-013C — Signal Health

This boundary answers one question:

Is the latest stabilized MediaHealth current-state projection usable
as current evidence at the supplied operational time?

It does not mutate the stored projection and does not manufacture a
replacement MediaHealth object.

Semantics:

- missing current state -> UNKNOWN;
- fresh current state -> stored MediaHealth.status;
- stale current state -> UNKNOWN;
- exact freshness boundary remains fresh;
- known stored negative states are preserved while fresh;
- freshness is evaluated against an explicit caller-supplied clock.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import MediaHealth
from app.noc.current_state.media_health_current_state import (
    MediaHealthCurrentState,
)
from app.noc.current_state.media_health_current_state_resolver import (
    MediaHealthCurrentStateResolver,
)
from app.noc.current_state.media_health_freshness import (
    MediaHealthFreshnessPolicy,
)


NOW = datetime(
    2026,
    9,
    24,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


def _health(
    status: HealthStatus = HealthStatus.HEALTHY,
) -> MediaHealth:
    return MediaHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        status=status,
    )


def _state(
    *,
    age_seconds: float,
    status: HealthStatus = HealthStatus.HEALTHY,
) -> MediaHealthCurrentState:
    return MediaHealthCurrentState(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        observed_at=(
            NOW - timedelta(seconds=age_seconds)
        ),
        health=_health(status),
    )


def _resolver(
    max_age_seconds: float = 16.0,
) -> MediaHealthCurrentStateResolver:
    return MediaHealthCurrentStateResolver(
        freshness_policy=MediaHealthFreshnessPolicy(
            max_age_seconds=max_age_seconds,
        )
    )


def test_missing_current_state_resolves_unknown() -> None:
    result = _resolver().resolve(
        state=None,
        now=NOW,
    )

    assert result is HealthStatus.UNKNOWN


def test_fresh_healthy_state_preserves_healthy() -> None:
    result = _resolver().resolve(
        state=_state(
            age_seconds=8.0,
            status=HealthStatus.HEALTHY,
        ),
        now=NOW,
    )

    assert result is HealthStatus.HEALTHY


@pytest.mark.parametrize(
    "status",
    [
        HealthStatus.DEGRADED,
        HealthStatus.CRITICAL,
        HealthStatus.UNKNOWN,
    ],
)
def test_fresh_state_preserves_stored_status(
    status: HealthStatus,
) -> None:
    result = _resolver().resolve(
        state=_state(
            age_seconds=8.0,
            status=status,
        ),
        now=NOW,
    )

    assert result is status


def test_exact_freshness_boundary_is_fresh() -> None:
    result = _resolver().resolve(
        state=_state(
            age_seconds=16.0,
            status=HealthStatus.HEALTHY,
        ),
        now=NOW,
    )

    assert result is HealthStatus.HEALTHY


@pytest.mark.parametrize(
    "stored_status",
    [
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthStatus.CRITICAL,
        HealthStatus.UNKNOWN,
    ],
)
def test_stale_state_resolves_unknown(
    stored_status: HealthStatus,
) -> None:
    result = _resolver().resolve(
        state=_state(
            age_seconds=16.000001,
            status=stored_status,
        ),
        now=NOW,
    )

    assert result is HealthStatus.UNKNOWN


def test_resolver_does_not_mutate_current_state() -> None:
    state = _state(
        age_seconds=8.0,
        status=HealthStatus.DEGRADED,
    )

    original_observed_at = state.observed_at
    original_health = state.health

    result = _resolver().resolve(
        state=state,
        now=NOW,
    )

    assert result is HealthStatus.DEGRADED
    assert state.observed_at == original_observed_at
    assert state.health is original_health
    assert state.health.status is HealthStatus.DEGRADED


def test_future_state_error_is_preserved_from_freshness_policy() -> None:
    state = MediaHealthCurrentState(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        observed_at=NOW + timedelta(seconds=1),
        health=_health(),
    )

    with pytest.raises(
        ValueError,
        match="future",
    ):
        _resolver().resolve(
            state=state,
            now=NOW,
        )


def test_naive_now_is_rejected_when_state_exists() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        _resolver().resolve(
            state=_state(age_seconds=8.0),
            now=datetime(2026, 9, 24, 12, 0, 0),
        )


def test_wrong_state_type_is_rejected() -> None:
    with pytest.raises(TypeError):
        _resolver().resolve(
            state="not-state",  # type: ignore[arg-type]
            now=NOW,
        )


def test_constructor_requires_freshness_policy() -> None:
    with pytest.raises(TypeError):
        MediaHealthCurrentStateResolver(
            freshness_policy="not-policy",  # type: ignore[arg-type]
        )
