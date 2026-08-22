"""Critical multimedia path reader evaluation for the NOC.

ENG-013B — Node SDK

CriticalPathReaderEvaluator compares current multimedia sessions against
CriticalPathPolicy values and classifies the reader condition of each
enabled critical path.

It is stateless. It does not apply grace periods, maintain history,
raise alarms or persist state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.sessions import (
    ActiveSession,
    SessionRole,
    SessionSnapshot,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)


class CriticalPathReaderState(str, Enum):
    """Current reader/publication condition of a critical path."""

    INACTIVE = "INACTIVE"
    HAS_READERS = "HAS_READERS"
    NO_READERS = "NO_READERS"
    INCONSISTENT = "INCONSISTENT"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class CriticalPathReaderEvaluation:
    """Immutable evaluation result for one critical path."""

    policy: CriticalPathPolicy
    state: CriticalPathReaderState
    publishers: tuple[ActiveSession, ...]
    readers: tuple[ActiveSession, ...]

    def __post_init__(self) -> None:
        if not isinstance(
            self.policy,
            CriticalPathPolicy,
        ):
            raise TypeError(
                "policy must be a CriticalPathPolicy"
            )

        if not isinstance(
            self.state,
            CriticalPathReaderState,
        ):
            raise TypeError(
                "state must be a CriticalPathReaderState"
            )

        if not isinstance(self.publishers, tuple):
            raise TypeError(
                "publishers must be a tuple"
            )

        if not isinstance(self.readers, tuple):
            raise TypeError(
                "readers must be a tuple"
            )

        for session in self.publishers:
            if not isinstance(session, ActiveSession):
                raise TypeError(
                    "publishers must contain only "
                    "ActiveSession values"
                )

            if session.role is not SessionRole.PUBLISHER:
                raise ValueError(
                    "publishers must contain only "
                    "publisher sessions"
                )

        for session in self.readers:
            if not isinstance(session, ActiveSession):
                raise TypeError(
                    "readers must contain only "
                    "ActiveSession values"
                )

            if session.role is not SessionRole.READER:
                raise ValueError(
                    "readers must contain only "
                    "reader sessions"
                )

        if self.state is CriticalPathReaderState.INACTIVE:
            if self.publishers:
                raise ValueError(
                    "INACTIVE evaluation must not "
                    "contain publishers"
                )

            if self.readers:
                raise ValueError(
                    "INACTIVE evaluation must not "
                    "contain readers"
                )

        if self.state is CriticalPathReaderState.HAS_READERS:
            if not self.publishers:
                raise ValueError(
                    "HAS_READERS evaluation requires "
                    "at least one publisher"
                )

            if not self.readers:
                raise ValueError(
                    "HAS_READERS evaluation requires "
                    "at least one reader"
                )

        if self.state is CriticalPathReaderState.NO_READERS:
            if not self.publishers:
                raise ValueError(
                    "NO_READERS evaluation requires "
                    "at least one publisher"
                )

            if self.readers:
                raise ValueError(
                    "NO_READERS evaluation must not "
                    "contain readers"
                )

        if self.state is CriticalPathReaderState.INCONSISTENT:
            if self.publishers:
                raise ValueError(
                    "INCONSISTENT evaluation must not "
                    "contain publishers"
                )

            if not self.readers:
                raise ValueError(
                    "INCONSISTENT evaluation requires "
                    "at least one reader"
                )


class CriticalPathReaderEvaluator:
    """Evaluate critical-path reader conditions."""

    def evaluate(
        self,
        *,
        snapshot: SessionSnapshot,
        policies: tuple[
            CriticalPathPolicy,
            ...,
        ],
    ) -> tuple[
        CriticalPathReaderEvaluation,
        ...,
    ]:
        """Evaluate all enabled critical-path policies."""

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

        paths: set[str] = set()

        for policy in policies:
            if not isinstance(
                policy,
                CriticalPathPolicy,
            ):
                raise TypeError(
                    "policies must contain only "
                    "CriticalPathPolicy values"
                )

            if policy.path in paths:
                raise ValueError(
                    "policies must not contain duplicate "
                    "path values"
                )

            paths.add(policy.path)

        evaluations: list[
            CriticalPathReaderEvaluation
        ] = []

        for policy in sorted(
            policies,
            key=lambda item: item.path,
        ):
            if not policy.enabled:
                continue

            path_sessions = tuple(
                session
                for session in snapshot.sessions
                if session.path == policy.path
            )

            publishers = tuple(
                session
                for session in path_sessions
                if session.role is SessionRole.PUBLISHER
            )

            readers = tuple(
                session
                for session in path_sessions
                if session.role is SessionRole.READER
            )

            if not publishers and not readers:
                state = CriticalPathReaderState.INACTIVE
            elif publishers and readers:
                state = CriticalPathReaderState.HAS_READERS
            elif publishers and not readers:
                state = CriticalPathReaderState.NO_READERS
            else:
                state = CriticalPathReaderState.INCONSISTENT

            evaluations.append(
                CriticalPathReaderEvaluation(
                    policy=policy,
                    state=state,
                    publishers=publishers,
                    readers=readers,
                )
            )

        return tuple(evaluations)
