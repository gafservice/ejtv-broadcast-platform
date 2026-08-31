"""Temporal stabilization for critical-path traffic conditions.

ENG-013B — Node SDK

CriticalPathTrafficStabilizer tracks how long a critical multimedia
path has continuously remained STALLED.

Only STALLED accumulates temporal alarm eligibility.
HEALTHY, UNKNOWN and INACTIVE clear the stalled candidate.

This component does not raise, resolve or persist alarms.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.noc.services.critical_path_traffic_evaluator import (
    CriticalPathTrafficEvaluation,
    CriticalPathTrafficState,
)


@dataclass(frozen=True, slots=True)
class CriticalPathTrafficStabilization:
    """Temporal result for one critical-path traffic evaluation."""

    evaluation: CriticalPathTrafficEvaluation
    observed_at: datetime
    stalled_since: datetime | None
    confirmed_stalled: bool

    def __post_init__(self) -> None:
        if not isinstance(
            self.evaluation,
            CriticalPathTrafficEvaluation,
        ):
            raise TypeError(
                "evaluation must be a CriticalPathTrafficEvaluation"
            )

        if not isinstance(self.observed_at, datetime):
            raise TypeError(
                "observed_at must be a datetime"
            )

        if (
            self.observed_at.tzinfo is None
            or self.observed_at.utcoffset() is None
        ):
            raise ValueError(
                "observed_at must be timezone-aware"
            )

        if (
            self.stalled_since is not None
            and not isinstance(self.stalled_since, datetime)
        ):
            raise TypeError(
                "stalled_since must be a datetime or None"
            )

        if (
            self.stalled_since is not None
            and (
                self.stalled_since.tzinfo is None
                or self.stalled_since.utcoffset() is None
            )
        ):
            raise ValueError(
                "stalled_since must be timezone-aware"
            )

        if not isinstance(self.confirmed_stalled, bool):
            raise TypeError(
                "confirmed_stalled must be a bool"
            )

        if (
            self.evaluation.state
            is CriticalPathTrafficState.STALLED
        ):
            if self.stalled_since is None:
                raise ValueError(
                    "STALLED stabilization requires stalled_since"
                )
        else:
            if self.stalled_since is not None:
                raise ValueError(
                    "non-STALLED stabilization must not "
                    "have stalled_since"
                )

            if self.confirmed_stalled:
                raise ValueError(
                    "non-STALLED stabilization cannot be "
                    "confirmed stalled"
                )

        if (
            self.stalled_since is not None
            and self.stalled_since > self.observed_at
        ):
            raise ValueError(
                "stalled_since must not follow observed_at"
            )


@dataclass(slots=True)
class _CriticalPathTrafficTemporalState:
    """Mutable temporal state for one critical path."""

    last_observed_at: datetime
    stalled_since: datetime | None = None


class CriticalPathTrafficStabilizer:
    """Confirm continuously stalled critical paths."""

    def __init__(self) -> None:
        self._states: dict[
            str,
            _CriticalPathTrafficTemporalState,
        ] = {}

    def stabilize(
        self,
        *,
        evaluation: CriticalPathTrafficEvaluation,
        observed_at: datetime,
    ) -> CriticalPathTrafficStabilization:
        """Apply the traffic-stalled grace period."""

        if not isinstance(
            evaluation,
            CriticalPathTrafficEvaluation,
        ):
            raise TypeError(
                "evaluation must be a CriticalPathTrafficEvaluation"
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

        path = evaluation.policy.path
        state = self._states.get(path)

        if state is None:
            state = _CriticalPathTrafficTemporalState(
                last_observed_at=observed_at,
            )
            self._states[path] = state
        else:
            if observed_at < state.last_observed_at:
                raise ValueError(
                    "critical path observations must not "
                    "move backwards in time"
                )

            state.last_observed_at = observed_at

        if evaluation.state is not CriticalPathTrafficState.STALLED:
            state.stalled_since = None

            return CriticalPathTrafficStabilization(
                evaluation=evaluation,
                observed_at=observed_at,
                stalled_since=None,
                confirmed_stalled=False,
            )

        if state.stalled_since is None:
            state.stalled_since = observed_at

        confirmed = (
            observed_at - state.stalled_since
            >= evaluation.policy.traffic_stalled_grace_period
        )

        return CriticalPathTrafficStabilization(
            evaluation=evaluation,
            observed_at=observed_at,
            stalled_since=state.stalled_since,
            confirmed_stalled=confirmed,
        )

    def reset(
        self,
        path: str | None = None,
    ) -> None:
        """Forget temporal history for one path or all paths."""

        if path is None:
            self._states.clear()
            return

        if not isinstance(path, str):
            raise TypeError(
                "path must be a string or None"
            )

        normalized = path.strip()

        if not normalized:
            raise ValueError(
                "path must not be empty"
            )

        self._states.pop(
            normalized,
            None,
        )
