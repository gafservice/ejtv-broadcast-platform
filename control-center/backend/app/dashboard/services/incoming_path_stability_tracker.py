"""Observed availability transitions for incoming media paths.

This component counts observed availability interruptions and
recoveries independently for each path.

It does not infer physical reconnections, persist history,
raise alarms, or inspect media streams.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IncomingPathStability:
    """Counters derived from observed path availability transitions."""

    interruptions: int
    recoveries: int


@dataclass(slots=True)
class _PathState:
    """Mutable observation state for one incoming path."""

    available: bool
    interruptions: int = 0
    recoveries: int = 0


class IncomingPathStabilityTracker:
    """Track observed availability transitions by incoming path."""

    def __init__(self) -> None:
        self._paths: dict[str, _PathState] = {}

    def observe(
        self,
        *,
        path_name: str,
        available: bool | None,
    ) -> IncomingPathStability:
        """Observe one path without inferring unobserved transitions."""

        if not isinstance(path_name, str) or not path_name:
            raise ValueError(
                "path_name must be a non-empty string"
            )

        if available is not None and type(available) is not bool:
            raise TypeError(
                "available must be bool or None"
            )

        state = self._paths.get(path_name)

        # Unknown observations do not establish or change
        # the last known availability state.
        if available is None:
            if state is None:
                return IncomingPathStability(
                    interruptions=0,
                    recoveries=0,
                )

            return IncomingPathStability(
                interruptions=state.interruptions,
                recoveries=state.recoveries,
            )

        # The first known observation establishes the baseline.
        if state is None:
            state = _PathState(available=available)
            self._paths[path_name] = state

            return IncomingPathStability(
                interruptions=0,
                recoveries=0,
            )

        if state.available and not available:
            state.interruptions += 1

        elif not state.available and available:
            state.recoveries += 1

        state.available = available

        return IncomingPathStability(
            interruptions=state.interruptions,
            recoveries=state.recoveries,
        )
