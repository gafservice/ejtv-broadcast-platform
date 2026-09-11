"""Temporal observation window for RTMP connection health."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from app.domain.streaming import HealthStatus, RTMPConnectionHealth


@dataclass(slots=True)
class _RTMPWindowState:
    """Internal temporal state for one RTMP connection."""

    last_observed_at: datetime
    last_healthy_at: datetime | None = None


class RTMPConnectionHealthWindow:
    """Preserve recent valid RTMP health across short UNKNOWN gaps."""

    def __init__(
        self,
        *,
        window_seconds: float,
    ) -> None:
        window_seconds = float(window_seconds)

        if window_seconds < 0:
            raise ValueError("window_seconds must be non-negative")

        self._window = timedelta(seconds=window_seconds)
        self._states: dict[str, _RTMPWindowState] = {}

    def reset(
        self,
        connection_id: str | None = None,
    ) -> None:
        """Reset temporal state for one RTMP connection or all."""

        if connection_id is None:
            self._states.clear()
            return

        self._states.pop(connection_id, None)

    def stabilize(
        self,
        health: RTMPConnectionHealth,
        *,
        observed_at: datetime,
    ) -> RTMPConnectionHealth:
        """Return RTMP health stabilized over the observation window."""

        state = self._states.get(health.connection_id)

        if state is None:
            self._states[health.connection_id] = _RTMPWindowState(
                last_observed_at=observed_at,
                last_healthy_at=(
                    observed_at
                    if health.status is HealthStatus.HEALTHY
                    else None
                ),
            )
            return health

        if observed_at < state.last_observed_at:
            raise ValueError(
                "RTMP connection health observations must not "
                "move backwards in time"
            )

        state.last_observed_at = observed_at

        if health.status is HealthStatus.HEALTHY:
            state.last_healthy_at = observed_at
            return health

        if (
            health.status is HealthStatus.UNKNOWN
            and state.last_healthy_at is not None
            and observed_at - state.last_healthy_at < self._window
        ):
            return replace(
                health,
                status=HealthStatus.HEALTHY,
                message=(
                    "RTMP health preserved by recent valid "
                    "traffic evidence."
                ),
            )

        return health
