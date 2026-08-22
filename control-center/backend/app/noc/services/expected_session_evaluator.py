"""Expected multimedia session evaluation for the NOC.

ENG-013B — Node SDK

ExpectedSessionEvaluator compares operational session expectations against
one current SessionSnapshot.

It determines whether each enabled ExpectedSessionPolicy is PRESENT or
MISSING.

The evaluator is deliberately stateless. It does not apply grace periods,
maintain history, raise alarms, persist state or emit events.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.sessions import (
    ActiveSession,
    SessionSnapshot,
)
from app.noc.domain.expected_session_policy import (
    ExpectedSessionPolicy,
)


class ExpectedSessionState(str, Enum):
    """Current observation state of an expected session."""

    PRESENT = "PRESENT"
    MISSING = "MISSING"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ExpectedSessionEvaluation:
    """Immutable result for one expected-session policy."""

    policy: ExpectedSessionPolicy
    state: ExpectedSessionState
    matching_sessions: tuple[ActiveSession, ...]

    def __post_init__(self) -> None:
        if not isinstance(
            self.policy,
            ExpectedSessionPolicy,
        ):
            raise TypeError(
                "policy must be an ExpectedSessionPolicy"
            )

        if not isinstance(
            self.state,
            ExpectedSessionState,
        ):
            raise TypeError(
                "state must be an ExpectedSessionState"
            )

        if not isinstance(
            self.matching_sessions,
            tuple,
        ):
            raise TypeError(
                "matching_sessions must be a tuple"
            )

        for session in self.matching_sessions:
            if not isinstance(
                session,
                ActiveSession,
            ):
                raise TypeError(
                    "matching_sessions must contain "
                    "only ActiveSession values"
                )

        if (
            self.state is ExpectedSessionState.PRESENT
            and not self.matching_sessions
        ):
            raise ValueError(
                "PRESENT evaluation requires at least "
                "one matching session"
            )

        if (
            self.state is ExpectedSessionState.MISSING
            and self.matching_sessions
        ):
            raise ValueError(
                "MISSING evaluation must not contain "
                "matching sessions"
            )


class ExpectedSessionEvaluator:
    """Evaluate expected-session policies against current observation."""

    def evaluate(
        self,
        *,
        snapshot: SessionSnapshot,
        policies: tuple[
            ExpectedSessionPolicy,
            ...,
        ],
    ) -> tuple[
        ExpectedSessionEvaluation,
        ...,
    ]:
        """Evaluate all enabled policies deterministically."""

        if not isinstance(
            snapshot,
            SessionSnapshot,
        ):
            raise TypeError(
                "snapshot must be a SessionSnapshot"
            )

        if not isinstance(policies, tuple):
            raise TypeError(
                "policies must be a tuple"
            )

        policy_ids: set[str] = set()

        for policy in policies:
            if not isinstance(
                policy,
                ExpectedSessionPolicy,
            ):
                raise TypeError(
                    "policies must contain only "
                    "ExpectedSessionPolicy values"
                )

            if policy.policy_id in policy_ids:
                raise ValueError(
                    "policies must not contain duplicate "
                    "policy_id values"
                )

            policy_ids.add(policy.policy_id)

        evaluations: list[
            ExpectedSessionEvaluation
        ] = []

        for policy in sorted(
            policies,
            key=lambda item: item.policy_id,
        ):
            if not policy.enabled:
                continue

            matching_sessions = tuple(
                session
                for session in snapshot.sessions
                if policy.matches(session)
            )

            state = (
                ExpectedSessionState.PRESENT
                if matching_sessions
                else ExpectedSessionState.MISSING
            )

            evaluations.append(
                ExpectedSessionEvaluation(
                    policy=policy,
                    state=state,
                    matching_sessions=matching_sessions,
                )
            )

        return tuple(evaluations)
