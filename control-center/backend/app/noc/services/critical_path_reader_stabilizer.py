"""Temporal stabilization for critical-path reader conditions.

ENG-013B — Node SDK

CriticalPathReaderStabilizer tracks how long a critical multimedia path
has continuously remained in NO_READERS state.

Only NO_READERS accumulates temporal alarm eligibility.
HAS_READERS and INACTIVE clear the no-readers candidate.

This component does not raise, resolve or persist alarms.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.noc.services.critical_path_reader_evaluator import (
    CriticalPathReaderEvaluation,
    CriticalPathReaderState,
)


@dataclass(frozen=True, slots=True)
class CriticalPathReaderStabilization:
    """Temporal result for one critical-path evaluation."""

    evaluation: CriticalPathReaderEvaluation
    observed_at: datetime
    no_readers_since: datetime | None
    confirmed_no_readers: bool

    def __post_init__(self) -> None:
        if not isinstance(
            self.evaluation,
            CriticalPathReaderEvaluation,
        ):
            raise TypeError(
                "evaluation must be a "
                "CriticalPathReaderEvaluation"
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
            self.no_readers_since is not None
            and not isinstance(
                self.no_readers_since,
                datetime,
            )
        ):
            raise TypeError(
                "no_readers_since must be a datetime or None"
            )

        if (
            self.no_readers_since is not None
            and (
                self.no_readers_since.tzinfo is None
                or self.no_readers_since.utcoffset() is None
            )
        ):
            raise ValueError(
                "no_readers_since must be timezone-aware"
            )

        if not isinstance(
            self.confirmed_no_readers,
            bool,
        ):
            raise TypeError(
                "confirmed_no_readers must be a bool"
            )

        if (
            self.evaluation.state
            is CriticalPathReaderState.NO_READERS
        ):
            if self.no_readers_since is None:
                raise ValueError(
                    "NO_READERS stabilization requires "
                    "no_readers_since"
                )
        else:
            if self.no_readers_since is not None:
                raise ValueError(
                    "non-NO_READERS stabilization must not "
                    "have no_readers_since"
                )

            if self.confirmed_no_readers:
                raise ValueError(
                    "non-NO_READERS stabilization cannot be "
                    "confirmed no readers"
                )

        if (
            self.no_readers_since is not None
            and self.no_readers_since > self.observed_at
        ):
            raise ValueError(
                "no_readers_since must not follow observed_at"
            )


@dataclass(slots=True)
class _CriticalPathTemporalState:
    """Mutable temporal state for one critical path."""

    last_observed_at: datetime
    no_readers_since: datetime | None = None


class CriticalPathReaderStabilizer:
    """Confirm continuously readerless critical paths."""

    def __init__(self) -> None:
        self._states: dict[
            str,
            _CriticalPathTemporalState,
        ] = {}

    def stabilize(
        self,
        *,
        evaluation: CriticalPathReaderEvaluation,
        observed_at: datetime,
    ) -> CriticalPathReaderStabilization:
        """Apply the no-readers grace period."""

        if not isinstance(
            evaluation,
            CriticalPathReaderEvaluation,
        ):
            raise TypeError(
                "evaluation must be a "
                "CriticalPathReaderEvaluation"
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
            state = _CriticalPathTemporalState(
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
            is not CriticalPathReaderState.NO_READERS
        ):
            state.no_readers_since = None

            return CriticalPathReaderStabilization(
                evaluation=evaluation,
                observed_at=observed_at,
                no_readers_since=None,
                confirmed_no_readers=False,
            )

        if state.no_readers_since is None:
            state.no_readers_since = observed_at

        confirmed = (
            observed_at - state.no_readers_since
            >= evaluation.policy.no_readers_grace_period
        )

        return CriticalPathReaderStabilization(
            evaluation=evaluation,
            observed_at=observed_at,
            no_readers_since=state.no_readers_since,
            confirmed_no_readers=confirmed,
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
