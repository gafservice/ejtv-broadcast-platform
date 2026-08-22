"""Reconnect flapping evaluation for multimedia sessions.

ENG-013B — Node SDK

ReconnectFlappingEvaluator correlates concrete session lifecycle
transitions into logical reconnect events and determines whether a
logical multimedia relationship is flapping.

A reconnect is counted when:

- a DISCONNECTED transition is observed;
- a later CONNECTED transition has the same LogicalSessionIdentity;
- the elapsed time does not exceed policy.reconnect_timeout.

Reconnect timestamps are retained only inside policy.window.

This component maintains temporal evaluation state but does not raise,
resolve or persist alarms.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from app.noc.domain.logical_session_identity import (
    LogicalSessionIdentity,
)
from app.noc.domain.reconnect_flapping_policy import (
    ReconnectFlappingPolicy,
)
from app.noc.services.session_transition_detector import (
    SessionTransition,
    SessionTransitionKind,
)


class ReconnectFlappingState(str, Enum):
    """Operational reconnect stability state."""

    STABLE = "STABLE"
    FLAPPING = "FLAPPING"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ReconnectFlappingEvaluation:
    """Immutable reconnect flapping evaluation result."""

    identity: LogicalSessionIdentity
    state: ReconnectFlappingState
    observed_at: datetime
    reconnect_count: int
    reconnect_timestamps: tuple[datetime, ...]
    reconnect_detected: bool

    def __post_init__(self) -> None:
        if not isinstance(
            self.identity,
            LogicalSessionIdentity,
        ):
            raise TypeError(
                "identity must be a LogicalSessionIdentity"
            )

        if not isinstance(
            self.state,
            ReconnectFlappingState,
        ):
            raise TypeError(
                "state must be a ReconnectFlappingState"
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

        if not isinstance(self.reconnect_count, int):
            raise TypeError(
                "reconnect_count must be an int"
            )

        if isinstance(self.reconnect_count, bool):
            raise TypeError(
                "reconnect_count must be an int"
            )

        if self.reconnect_count < 0:
            raise ValueError(
                "reconnect_count must not be negative"
            )

        if not isinstance(
            self.reconnect_timestamps,
            tuple,
        ):
            raise TypeError(
                "reconnect_timestamps must be a tuple"
            )

        for timestamp in self.reconnect_timestamps:
            if not isinstance(timestamp, datetime):
                raise TypeError(
                    "reconnect_timestamps must contain "
                    "only datetime values"
                )

            if (
                timestamp.tzinfo is None
                or timestamp.utcoffset() is None
            ):
                raise ValueError(
                    "reconnect timestamps must be "
                    "timezone-aware"
                )

        if (
            self.reconnect_count
            != len(self.reconnect_timestamps)
        ):
            raise ValueError(
                "reconnect_count must equal the number "
                "of reconnect_timestamps"
            )

        if not isinstance(
            self.reconnect_detected,
            bool,
        ):
            raise TypeError(
                "reconnect_detected must be a bool"
            )


@dataclass(slots=True)
class _ReconnectState:
    """Mutable temporal state for one logical session identity."""

    last_observed_at: datetime
    pending_disconnect_at: datetime | None
    reconnect_timestamps: list[datetime]


class ReconnectFlappingEvaluator:
    """Correlate session transitions and detect reconnect flapping."""

    def __init__(
        self,
        *,
        policy: ReconnectFlappingPolicy | None = None,
    ) -> None:
        if (
            policy is not None
            and not isinstance(
                policy,
                ReconnectFlappingPolicy,
            )
        ):
            raise TypeError(
                "policy must be a "
                "ReconnectFlappingPolicy or None"
            )

        self._policy = (
            policy
            if policy is not None
            else ReconnectFlappingPolicy()
        )

        self._states: dict[
            LogicalSessionIdentity,
            _ReconnectState,
        ] = {}

    @property
    def policy(self) -> ReconnectFlappingPolicy:
        return self._policy

    def evaluate(
        self,
        *,
        transition: SessionTransition,
        observed_at: datetime,
    ) -> ReconnectFlappingEvaluation:
        """Process one session lifecycle transition."""

        if not isinstance(
            transition,
            SessionTransition,
        ):
            raise TypeError(
                "transition must be a SessionTransition"
            )

        self._validate_timestamp(observed_at)

        identity = LogicalSessionIdentity.from_session(
            transition.session
        )

        state = self._states.get(identity)

        if state is None:
            state = _ReconnectState(
                last_observed_at=observed_at,
                pending_disconnect_at=None,
                reconnect_timestamps=[],
            )
            self._states[identity] = state
        else:
            if observed_at < state.last_observed_at:
                raise ValueError(
                    "reconnect observations must not "
                    "move backwards in time"
                )

            state.last_observed_at = observed_at

        self._prune(
            state,
            observed_at,
        )

        reconnect_detected = False

        if (
            transition.kind
            is SessionTransitionKind.DISCONNECTED
        ):
            state.pending_disconnect_at = observed_at

        elif (
            transition.kind
            is SessionTransitionKind.CONNECTED
        ):
            pending = state.pending_disconnect_at

            if pending is not None:
                elapsed = observed_at - pending

                if (
                    timedelta(0)
                    <= elapsed
                    <= self._policy.reconnect_timeout
                ):
                    state.reconnect_timestamps.append(
                        observed_at
                    )
                    reconnect_detected = True

                state.pending_disconnect_at = None

        self._prune(
            state,
            observed_at,
        )

        reconnect_timestamps = tuple(
            state.reconnect_timestamps
        )

        flapping = (
            len(reconnect_timestamps)
            >= self._policy.threshold
        )

        return ReconnectFlappingEvaluation(
            identity=identity,
            state=(
                ReconnectFlappingState.FLAPPING
                if flapping
                else ReconnectFlappingState.STABLE
            ),
            observed_at=observed_at,
            reconnect_count=len(
                reconnect_timestamps
            ),
            reconnect_timestamps=reconnect_timestamps,
            reconnect_detected=reconnect_detected,
        )

    def identities(
        self,
    ) -> tuple[LogicalSessionIdentity, ...]:
        """Return known logical session identities deterministically."""

        return tuple(
            sorted(
                self._states,
                key=lambda identity: (
                    identity.protocol.value,
                    identity.role.value,
                    identity.path or "",
                    identity.remote_ip,
                ),
            )
        )

    def observe(
        self,
        *,
        identity: LogicalSessionIdentity,
        observed_at: datetime,
    ) -> ReconnectFlappingEvaluation:
        """Advance temporal evaluation without a new transition."""

        if not isinstance(
            identity,
            LogicalSessionIdentity,
        ):
            raise TypeError(
                "identity must be a LogicalSessionIdentity"
            )

        self._validate_timestamp(observed_at)

        state = self._states.get(identity)

        if state is None:
            state = _ReconnectState(
                last_observed_at=observed_at,
                pending_disconnect_at=None,
                reconnect_timestamps=[],
            )
            self._states[identity] = state
        else:
            if observed_at < state.last_observed_at:
                raise ValueError(
                    "reconnect observations must not "
                    "move backwards in time"
                )

            state.last_observed_at = observed_at

        self._prune(
            state,
            observed_at,
        )

        reconnect_timestamps = tuple(
            state.reconnect_timestamps
        )

        return ReconnectFlappingEvaluation(
            identity=identity,
            state=(
                ReconnectFlappingState.FLAPPING
                if (
                    len(reconnect_timestamps)
                    >= self._policy.threshold
                )
                else ReconnectFlappingState.STABLE
            ),
            observed_at=observed_at,
            reconnect_count=len(
                reconnect_timestamps
            ),
            reconnect_timestamps=reconnect_timestamps,
            reconnect_detected=False,
        )

    def reset(
        self,
        identity: LogicalSessionIdentity | None = None,
    ) -> None:
        """Forget reconnect history for one identity or all identities."""

        if identity is None:
            self._states.clear()
            return

        if not isinstance(
            identity,
            LogicalSessionIdentity,
        ):
            raise TypeError(
                "identity must be a "
                "LogicalSessionIdentity or None"
            )

        self._states.pop(
            identity,
            None,
        )

    def _prune(
        self,
        state: _ReconnectState,
        observed_at: datetime,
    ) -> None:
        cutoff = (
            observed_at - self._policy.window
        )

        state.reconnect_timestamps[:] = [
            timestamp
            for timestamp in state.reconnect_timestamps
            if timestamp >= cutoff
        ]

        if (
            state.pending_disconnect_at is not None
            and (
                observed_at
                - state.pending_disconnect_at
                > self._policy.reconnect_timeout
            )
        ):
            state.pending_disconnect_at = None

    @staticmethod
    def _validate_timestamp(
        timestamp: datetime,
    ) -> None:
        if not isinstance(timestamp, datetime):
            raise TypeError(
                "observed_at must be a datetime"
            )

        if (
            timestamp.tzinfo is None
            or timestamp.utcoffset() is None
        ):
            raise ValueError(
                "observed_at must be timezone-aware"
            )
