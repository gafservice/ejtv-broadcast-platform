"""Temporal stabilization for critical-path availability conditions.

ENG-013B — Node SDK

CriticalPathAvailabilityStabilizer tracks how long a critical multimedia
path has continuously remained UNAVAILABLE.

Only UNAVAILABLE accumulates temporal alarm eligibility.
AVAILABLE clears the unavailable candidate.

This component does not raise, resolve or persist alarms.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.noc.services.critical_path_availability_evaluator import (
    CriticalPathAvailabilityEvaluation,
    CriticalPathAvailabilityState,
)


@dataclass(frozen=True, slots=True)
class CriticalPathAvailabilityStabilization:
    """Temporal result for one critical-path availability evaluation."""

    evaluation: CriticalPathAvailabilityEvaluation
    observed_at: datetime
    unavailable_since: datetime | None
    confirmed_unavailable: bool

    def __post_init__(self) -> None:
        if not isinstance(
            self.evaluation,
            CriticalPathAvailabilityEvaluation,
        ):
            raise TypeError(
                "evaluation must be a "
                "CriticalPathAvailabilityEvaluation"
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
            self.unavailable_since is not None
            and not isinstance(
                self.unavailable_since,
                datetime,
            )
        ):
            raise TypeError(
                "unavailable_since must be a datetime or None"
            )

        if (
            self.unavailable_since is not None
            and (
                self.unavailable_since.tzinfo is None
                or self.unavailable_since.utcoffset() is None
            )
        ):
            raise ValueError(
                "unavailable_since must be timezone-aware"
            )

        if not isinstance(
            self.confirmed_unavailable,
            bool,
        ):
            raise TypeError(
                "confirmed_unavailable must be a bool"
            )

        if (
            self.evaluation.state
            is CriticalPathAvailabilityState.UNAVAILABLE
        ):
            if self.unavailable_since is None:
                raise ValueError(
                    "UNAVAILABLE stabilization requires "
                    "unavailable_since"
                )
        else:
            if self.unavailable_since is not None:
                raise ValueError(
                    "non-UNAVAILABLE stabilization must not "
                    "have unavailable_since"
                )

            if self.confirmed_unavailable:
                raise ValueError(
                    "non-UNAVAILABLE stabilization cannot be "
                    "confirmed unavailable"
                )

        if (
            self.unavailable_since is not None
            and self.unavailable_since > self.observed_at
        ):
            raise ValueError(
                "unavailable_since must not follow observed_at"
            )


@dataclass(slots=True)
class _CriticalPathAvailabilityTemporalState:
    """Mutable temporal state for one critical path."""

    last_observed_at: datetime
    unavailable_since: datetime | None = None


class CriticalPathAvailabilityStabilizer:
    """Confirm continuously unavailable critical paths."""

    def __init__(self) -> None:
        self._states: dict[
            str,
            _CriticalPathAvailabilityTemporalState,
        ] = {}

    def stabilize(
        self,
        *,
        evaluation: CriticalPathAvailabilityEvaluation,
        observed_at: datetime,
    ) -> CriticalPathAvailabilityStabilization:
        """Apply the unavailable grace period."""

        if not isinstance(
            evaluation,
            CriticalPathAvailabilityEvaluation,
        ):
            raise TypeError(
                "evaluation must be a "
                "CriticalPathAvailabilityEvaluation"
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
            state = _CriticalPathAvailabilityTemporalState(
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

        if (
            evaluation.state
            is not CriticalPathAvailabilityState.UNAVAILABLE
        ):
            state.unavailable_since = None

            return CriticalPathAvailabilityStabilization(
                evaluation=evaluation,
                observed_at=observed_at,
                unavailable_since=None,
                confirmed_unavailable=False,
            )

        if state.unavailable_since is None:
            state.unavailable_since = observed_at

        confirmed = (
            observed_at - state.unavailable_since
            >= evaluation.policy.unavailable_grace_period
        )

        return CriticalPathAvailabilityStabilization(
            evaluation=evaluation,
            observed_at=observed_at,
            unavailable_since=state.unavailable_since,
            confirmed_unavailable=confirmed,
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
