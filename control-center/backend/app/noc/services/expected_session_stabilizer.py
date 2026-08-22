"""Temporal stabilization for expected multimedia sessions.

ENG-013B — Node SDK

ExpectedSessionStabilizer tracks how long an expected multimedia session
has continuously remained missing.

It preserves the distinction between observation and alarm eligibility:

- ExpectedSessionEvaluation describes what is observed now.
- ExpectedSessionStabilization determines whether the missing condition
  has persisted long enough to be considered confirmed.

The stabilizer does not raise, resolve or persist alarms.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.noc.services.expected_session_evaluator import (
    ExpectedSessionEvaluation,
    ExpectedSessionState,
)


@dataclass(frozen=True, slots=True)
class ExpectedSessionStabilization:
    """Temporal result for one expected-session evaluation."""

    evaluation: ExpectedSessionEvaluation
    observed_at: datetime
    missing_since: datetime | None
    confirmed_missing: bool

    def __post_init__(self) -> None:
        if not isinstance(
            self.evaluation,
            ExpectedSessionEvaluation,
        ):
            raise TypeError(
                "evaluation must be an ExpectedSessionEvaluation"
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
            self.missing_since is not None
            and not isinstance(
                self.missing_since,
                datetime,
            )
        ):
            raise TypeError(
                "missing_since must be a datetime or None"
            )

        if (
            self.missing_since is not None
            and (
                self.missing_since.tzinfo is None
                or self.missing_since.utcoffset() is None
            )
        ):
            raise ValueError(
                "missing_since must be timezone-aware"
            )

        if not isinstance(self.confirmed_missing, bool):
            raise TypeError(
                "confirmed_missing must be a bool"
            )

        if (
            self.evaluation.state
            is ExpectedSessionState.PRESENT
        ):
            if self.missing_since is not None:
                raise ValueError(
                    "PRESENT stabilization must not have "
                    "missing_since"
                )

            if self.confirmed_missing:
                raise ValueError(
                    "PRESENT stabilization cannot be "
                    "confirmed missing"
                )

        if (
            self.evaluation.state
            is ExpectedSessionState.MISSING
            and self.missing_since is None
        ):
            raise ValueError(
                "MISSING stabilization requires missing_since"
            )

        if (
            self.missing_since is not None
            and self.missing_since > self.observed_at
        ):
            raise ValueError(
                "missing_since must not follow observed_at"
            )


@dataclass(slots=True)
class _ExpectedSessionTemporalState:
    """Mutable internal state for one policy."""

    last_observed_at: datetime
    missing_since: datetime | None = None


class ExpectedSessionStabilizer:
    """Confirm continuously missing expected sessions."""

    def __init__(self) -> None:
        self._states: dict[
            str,
            _ExpectedSessionTemporalState,
        ] = {}

    def stabilize(
        self,
        *,
        evaluation: ExpectedSessionEvaluation,
        observed_at: datetime,
    ) -> ExpectedSessionStabilization:
        """Apply the policy missing grace period."""

        if not isinstance(
            evaluation,
            ExpectedSessionEvaluation,
        ):
            raise TypeError(
                "evaluation must be an ExpectedSessionEvaluation"
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

        policy = evaluation.policy
        policy_id = policy.policy_id

        state = self._states.get(policy_id)

        if state is not None:
            if observed_at < state.last_observed_at:
                raise ValueError(
                    "expected session observations must not "
                    "move backwards in time"
                )

            state.last_observed_at = observed_at

        else:
            state = _ExpectedSessionTemporalState(
                last_observed_at=observed_at,
            )
            self._states[policy_id] = state

        if (
            evaluation.state
            is ExpectedSessionState.PRESENT
        ):
            state.missing_since = None

            return ExpectedSessionStabilization(
                evaluation=evaluation,
                observed_at=observed_at,
                missing_since=None,
                confirmed_missing=False,
            )

        if state.missing_since is None:
            state.missing_since = observed_at

        confirmed_missing = (
            observed_at - state.missing_since
            >= policy.missing_grace_period
        )

        return ExpectedSessionStabilization(
            evaluation=evaluation,
            observed_at=observed_at,
            missing_since=state.missing_since,
            confirmed_missing=confirmed_missing,
        )

    def reset(
        self,
        policy_id: str | None = None,
    ) -> None:
        """Forget temporal history for one policy or all policies."""

        if policy_id is None:
            self._states.clear()
            return

        if not isinstance(policy_id, str):
            raise TypeError(
                "policy_id must be a string or None"
            )

        normalized = policy_id.strip()

        if not normalized:
            raise ValueError(
                "policy_id must not be empty"
            )

        self._states.pop(
            normalized,
            None,
        )
