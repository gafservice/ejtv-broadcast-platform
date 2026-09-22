"""Temporal stabilization for Media Health.

ENG-013C — Media Health

This module applies temporal confirmation to instantaneous MediaHealth
results.

It does not:

- evaluate media observations;
- assign field-level media health;
- emit events or alarms;
- persist temporal state;
- integrate with runtime or dashboard concerns.

Time belongs to the stabilization call through ``observed_at`` and is
not added retroactively to MediaEvaluation or MediaHealth.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import MediaHealth


@dataclass(slots=True)
class _MediaHealthStabilizationState:
    """Internal temporal state for one media-health identity."""

    stable_status: HealthStatus
    last_observed_at: datetime
    candidate_status: HealthStatus | None = None
    candidate_since: datetime | None = None


class MediaHealthStabilizer:
    """Apply temporal hysteresis to effective Media Health."""

    def __init__(
        self,
        *,
        degradation_seconds: float,
        recovery_seconds: float,
    ) -> None:
        if isinstance(degradation_seconds, bool) or not isinstance(
            degradation_seconds,
            (int, float),
        ):
            raise TypeError(
                "degradation_seconds must be a number"
            )

        if isinstance(recovery_seconds, bool) or not isinstance(
            recovery_seconds,
            (int, float),
        ):
            raise TypeError(
                "recovery_seconds must be a number"
            )

        if degradation_seconds < 0:
            raise ValueError(
                "degradation_seconds must be non-negative"
            )

        if recovery_seconds < 0:
            raise ValueError(
                "recovery_seconds must be non-negative"
            )

        self._degradation_delay = timedelta(
            seconds=float(degradation_seconds)
        )
        self._recovery_delay = timedelta(
            seconds=float(recovery_seconds)
        )

        self._states: dict[
            tuple[str, str, str | None],
            _MediaHealthStabilizationState,
        ] = {}

    def stabilize(
        self,
        health: MediaHealth,
        *,
        observed_at: datetime,
    ) -> MediaHealth:
        """Return temporally stabilized Media Health."""

        if not isinstance(health, MediaHealth):
            raise TypeError(
                "health must be a MediaHealth"
            )

        if not isinstance(observed_at, datetime):
            raise TypeError(
                "observed_at must be a datetime"
            )

        if (
            observed_at.tzinfo is None
            or observed_at.utcoffset() is None
        ):
            raise ValueError(
                "observed_at must be timezone-aware"
            )

        identity = (
            health.profile_id,
            health.service_id,
            health.path_name,
        )

        state = self._states.get(identity)

        if state is None:
            self._states[identity] = (
                _MediaHealthStabilizationState(
                    stable_status=health.status,
                    last_observed_at=observed_at,
                )
            )
            return health

        if observed_at < state.last_observed_at:
            raise ValueError(
                "media health observations must not "
                "move backwards in time"
            )

        state.last_observed_at = observed_at

        if health.status is state.stable_status:
            state.candidate_status = None
            state.candidate_since = None
            return health

        required_delay = (
            self._recovery_delay
            if health.status is HealthStatus.HEALTHY
            else self._degradation_delay
        )

        if (
            state.candidate_status is not health.status
            or state.candidate_since is None
        ):
            state.candidate_status = health.status
            state.candidate_since = observed_at

            if required_delay == timedelta(0):
                state.stable_status = health.status
                state.candidate_status = None
                state.candidate_since = None
                return health

            return replace(
                health,
                status=state.stable_status,
            )

        if (
            observed_at - state.candidate_since
            >= required_delay
        ):
            state.stable_status = health.status
            state.candidate_status = None
            state.candidate_since = None
            return health

        return replace(
            health,
            status=state.stable_status,
        )

    def reset(
        self,
        *,
        profile_id: str | None = None,
        service_id: str | None = None,
        path_name: str | None = None,
    ) -> None:
        """Forget stabilization history.

        With no identity arguments all temporal state is cleared.
        With identity arguments, the exact media-health identity is cleared.
        """

        if (
            profile_id is None
            and service_id is None
            and path_name is None
        ):
            self._states.clear()
            return

        if not isinstance(profile_id, str):
            raise TypeError(
                "profile_id must be a string"
            )

        if not isinstance(service_id, str):
            raise TypeError(
                "service_id must be a string"
            )

        normalized_profile = profile_id.strip()
        normalized_service = service_id.strip()

        if not normalized_profile:
            raise ValueError(
                "profile_id must not be empty"
            )

        if not normalized_service:
            raise ValueError(
                "service_id must not be empty"
            )

        if path_name is not None:
            if not isinstance(path_name, str):
                raise TypeError(
                    "path_name must be a string or None"
                )

            path_name = path_name.strip()

            if not path_name:
                raise ValueError(
                    "path_name must not be empty"
                )

        self._states.pop(
            (
                normalized_profile,
                normalized_service,
                path_name,
            ),
            None,
        )
