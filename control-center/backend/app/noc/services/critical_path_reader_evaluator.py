"""Critical multimedia path reader evaluation for the NOC.

ENG-013B — Node SDK

CriticalPathReaderEvaluator evaluates critical multimedia paths from the
normalized MediaMTX path snapshot.

MediaMTXSnapshot is the source of truth for publication state and reader
presence. SessionSnapshot is deliberately not used here because some
MediaMTX sources, such as mpegtsSource, are not represented as ordinary
publisher sessions.

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


class CriticalPathReaderState(str, Enum):
    """Current reader/publication condition of a critical path."""

    INACTIVE = "INACTIVE"
    HAS_READERS = "HAS_READERS"
    NO_READERS = "NO_READERS"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class CriticalPathReaderEvaluation:
    """Immutable evaluation result for one critical path."""

    policy: CriticalPathPolicy
    state: CriticalPathReaderState
    media_path: MediaPath | None

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

        if (
            self.media_path is not None
            and not isinstance(
                self.media_path,
                MediaPath,
            )
        ):
            raise TypeError(
                "media_path must be a MediaPath or None"
            )

        if self.state is CriticalPathReaderState.INACTIVE:
            return

        if self.media_path is None:
            raise ValueError(
                "active critical-path evaluation requires "
                "a media_path"
            )

        if not self.media_path.is_active:
            raise ValueError(
                "active critical-path evaluation requires "
                "an active media_path"
            )

        if not self.media_path.has_source:
            raise ValueError(
                "active critical-path evaluation requires "
                "a media source"
            )

        if self.state is CriticalPathReaderState.HAS_READERS:
            if self.media_path.reader_count < 1:
                raise ValueError(
                    "HAS_READERS evaluation requires "
                    "at least one reader"
                )

        if self.state is CriticalPathReaderState.NO_READERS:
            if self.media_path.reader_count != 0:
                raise ValueError(
                    "NO_READERS evaluation requires "
                    "zero readers"
                )


class CriticalPathReaderEvaluator:
    """Evaluate critical paths from normalized MediaMTX state."""

    def evaluate(
        self,
        *,
        snapshot: MediaMTXSnapshot,
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
            MediaMTXSnapshot,
        ):
            raise TypeError(
                "snapshot must be a MediaMTXSnapshot"
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

            media_path = snapshot.get_path(
                policy.path
            )

            if (
                media_path is None
                or not media_path.is_active
                or not media_path.has_source
            ):
                state = (
                    CriticalPathReaderState.INACTIVE
                )
            elif media_path.reader_count > 0:
                state = (
                    CriticalPathReaderState.HAS_READERS
                )
            else:
                state = (
                    CriticalPathReaderState.NO_READERS
                )

            evaluations.append(
                CriticalPathReaderEvaluation(
                    policy=policy,
                    state=state,
                    media_path=media_path,
                )
            )

        return tuple(evaluations)
