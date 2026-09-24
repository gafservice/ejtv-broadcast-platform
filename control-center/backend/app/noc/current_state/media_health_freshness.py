"""Freshness policy for Media Health current-state projections.

ENG-013C — Signal Health

The current-state repository owns only the latest known stabilized
MediaHealth projection.

Freshness is a consumer-side temporal decision: it determines whether
that projection is recent enough to participate in a current
Signal Health decision.

A stale projection is not itself DEGRADED or CRITICAL. It represents
insufficient current evidence and must therefore be treated by the
consumer as unavailable current Media Health evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite

from app.noc.current_state.media_health_current_state import (
    MediaHealthCurrentState,
)


@dataclass(frozen=True, slots=True)
class MediaHealthFreshnessPolicy:
    """Decide whether a Media Health current-state projection is fresh."""

    max_age_seconds: float

    def __post_init__(self) -> None:
        value = self.max_age_seconds

        if isinstance(value, bool) or not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                "max_age_seconds must be a finite number"
            )

        normalized = float(value)

        if not isfinite(normalized):
            raise ValueError(
                "max_age_seconds must be finite"
            )

        if normalized < 0:
            raise ValueError(
                "max_age_seconds must be non-negative"
            )

        object.__setattr__(
            self,
            "max_age_seconds",
            normalized,
        )

    def is_fresh(
        self,
        *,
        state: MediaHealthCurrentState,
        now: datetime,
    ) -> bool:
        """Return whether state is recent enough at ``now``."""

        if not isinstance(
            state,
            MediaHealthCurrentState,
        ):
            raise TypeError(
                "state must be a MediaHealthCurrentState"
            )

        if not isinstance(now, datetime):
            raise TypeError(
                "now must be a datetime"
            )

        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError(
                "now must be timezone-aware"
            )

        age_seconds = (
            now - state.observed_at
        ).total_seconds()

        if age_seconds < 0:
            raise ValueError(
                "state observed_at cannot be in the future"
            )

        return age_seconds <= self.max_age_seconds
