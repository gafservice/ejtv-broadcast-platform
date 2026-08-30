"""Critical multimedia path availability evaluation for the NOC.

ENG-013B — Node SDK

CriticalPathAvailabilityEvaluator determines whether an enabled critical
multimedia path is operationally available from the normalized MediaMTX
snapshot.

MediaMTXSnapshot and MediaPath are the source of truth for path and source
availability. Reader presence and traffic health are deliberately outside
the scope of this evaluator.

The evaluator is stateless. It does not apply grace periods, maintain
history, raise alarms or persist state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.streaming.models import (
    MediaMTXSnapshot,
    MediaPath,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)


class CriticalPathAvailabilityState(str, Enum):
    """Current availability condition of a critical multimedia path."""

    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class CriticalPathAvailabilityEvaluation:
    """Immutable availability evaluation for one critical path."""

    policy: CriticalPathPolicy
    state: CriticalPathAvailabilityState
    media_path: MediaPath | None

    def __post_init__(self) -> None:
        if not isinstance(self.policy, CriticalPathPolicy):
            raise TypeError(
                "policy must be a CriticalPathPolicy"
            )

        if not isinstance(
            self.state,
            CriticalPathAvailabilityState,
        ):
            raise TypeError(
                "state must be a CriticalPathAvailabilityState"
            )

        if (
            self.media_path is not None
            and not isinstance(self.media_path, MediaPath)
        ):
            raise TypeError(
                "media_path must be a MediaPath or None"
            )

        if (
            self.state
            is CriticalPathAvailabilityState.AVAILABLE
        ):
            if self.media_path is None:
                raise ValueError(
                    "AVAILABLE evaluation requires a media_path"
                )

            if not self.media_path.is_active:
                raise ValueError(
                    "AVAILABLE evaluation requires an active media_path"
                )

            if not self.media_path.has_source:
                raise ValueError(
                    "AVAILABLE evaluation requires a media source"
                )

            if not self.media_path.ready:
                raise ValueError(
                    "AVAILABLE evaluation requires ready=True"
                )

            if not self.media_path.available:
                raise ValueError(
                    "AVAILABLE evaluation requires available=True"
                )

            if not self.media_path.online:
                raise ValueError(
                    "AVAILABLE evaluation requires online=True"
                )


class CriticalPathAvailabilityEvaluator:
    """Evaluate critical-path availability from normalized MediaMTX state."""

    def evaluate(
        self,
        *,
        snapshot: MediaMTXSnapshot,
        policies: tuple[CriticalPathPolicy, ...],
    ) -> tuple[CriticalPathAvailabilityEvaluation, ...]:
        """Evaluate all enabled critical-path policies."""

        if not isinstance(snapshot, MediaMTXSnapshot):
            raise TypeError(
                "snapshot must be a MediaMTXSnapshot"
            )

        if not isinstance(policies, tuple):
            raise TypeError(
                "policies must be a tuple"
            )

        paths: set[str] = set()

        for policy in policies:
            if not isinstance(policy, CriticalPathPolicy):
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
            CriticalPathAvailabilityEvaluation
        ] = []

        for policy in sorted(
            policies,
            key=lambda item: item.path,
        ):
            if not policy.enabled:
                continue

            media_path = snapshot.get_path(policy.path)

            if (
                media_path is not None
                and media_path.is_active
                and media_path.has_source
                and media_path.ready
                and media_path.available
                and media_path.online
            ):
                state = CriticalPathAvailabilityState.AVAILABLE
            else:
                state = CriticalPathAvailabilityState.UNAVAILABLE

            evaluations.append(
                CriticalPathAvailabilityEvaluation(
                    policy=policy,
                    state=state,
                    media_path=media_path,
                )
            )

        return tuple(evaluations)
