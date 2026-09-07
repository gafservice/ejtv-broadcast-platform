"""Temporal stabilization of effective SRT connection health.

ENG-013B — Stream Health Block 2

This service keeps instantaneous SRT connection evidence while preventing
short-lived health fluctuations from immediately replacing the committed
effective health state.

It does not create events or alarms.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from app.domain.streaming.health import (
    HealthStatus,
    SRTConnectionHealth,
)


@dataclass(slots=True)
class _ConnectionStabilizationState:
    """Internal temporal state for one SRT connection."""

    stable_status: HealthStatus
    last_observed_at: datetime
    candidate_status: HealthStatus | None = None
    candidate_since: datetime | None = None


class SRTConnectionHealthStabilizer:
    """Apply temporal hysteresis to effective SRT connection health."""

    def __init__(
        self,
        *,
        degradation_seconds: float,
        recovery_seconds: float,
    ) -> None:
        degradation_seconds = float(degradation_seconds)
        recovery_seconds = float(recovery_seconds)

        if degradation_seconds < 0:
            raise ValueError(
                "degradation_seconds must be non-negative"
            )

        if recovery_seconds < 0:
            raise ValueError(
                "recovery_seconds must be non-negative"
            )

        self._degradation_delay = timedelta(
            seconds=degradation_seconds
        )
        self._recovery_delay = timedelta(
            seconds=recovery_seconds
        )

        self._states: dict[
            str,
            _ConnectionStabilizationState,
        ] = {}

    def reset(
        self,
        connection_id: str | None = None,
    ) -> None:
        """Reset temporal state for one connection or all connections."""

        if connection_id is None:
            self._states.clear()
            return

        self._states.pop(connection_id, None)

    def stabilize(
        self,
        health: SRTConnectionHealth,
        *,
        observed_at: datetime,
    ) -> SRTConnectionHealth:
        """Return effective health for the current SRT observation."""

        state = self._states.get(health.connection_id)

        if state is None:
            self._states[health.connection_id] = (
                _ConnectionStabilizationState(
                    stable_status=health.status,
                    last_observed_at=observed_at,
                )
            )
            return health

        if observed_at < state.last_observed_at:
            raise ValueError(
                "SRT connection health observations must not "
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
                message=(
                    f"Temporally stabilized at "
                    f"{state.stable_status.value}; "
                    f"current observation: {health.message}"
                ),
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
            message=(
                f"Temporally stabilized at "
                f"{state.stable_status.value}; "
                f"current observation: {health.message}"
            ),
        )
