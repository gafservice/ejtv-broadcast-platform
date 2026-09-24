"""Resolve effective Media Health from current-state freshness.

ENG-013C — Signal Health

The durable current-state repository stores the latest known stabilized
MediaHealth projection.

This resolver decides whether that projection is usable as current
evidence at an explicit operational time.

Semantics:

- missing current state -> UNKNOWN;
- fresh current state -> stored MediaHealth.status;
- stale current state -> UNKNOWN.

The resolver does not mutate current state, manufacture MediaHealth,
read persistence, own a clock, or calculate Signal Health.
"""

from __future__ import annotations

from datetime import datetime

from app.domain.streaming.health import HealthStatus
from app.noc.current_state.media_health_current_state import (
    MediaHealthCurrentState,
)
from app.noc.current_state.media_health_freshness import (
    MediaHealthFreshnessPolicy,
)


class MediaHealthCurrentStateResolver:
    """Resolve the effective status of current Media Health evidence."""

    def __init__(
        self,
        *,
        freshness_policy: MediaHealthFreshnessPolicy,
    ) -> None:
        if not isinstance(
            freshness_policy,
            MediaHealthFreshnessPolicy,
        ):
            raise TypeError(
                "freshness_policy must be a "
                "MediaHealthFreshnessPolicy"
            )

        self._freshness_policy = freshness_policy

    def resolve(
        self,
        *,
        state: MediaHealthCurrentState | None,
        now: datetime,
    ) -> HealthStatus:
        """Return effective Media Health status at ``now``."""

        if state is None:
            return HealthStatus.UNKNOWN

        if not isinstance(
            state,
            MediaHealthCurrentState,
        ):
            raise TypeError(
                "state must be a MediaHealthCurrentState or None"
            )

        if not self._freshness_policy.is_fresh(
            state=state,
            now=now,
        ):
            return HealthStatus.UNKNOWN

        return state.health.status
