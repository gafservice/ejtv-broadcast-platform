"""Critical multimedia path policy for the NOC.

ENG-013B — Node SDK

CriticalPathPolicy identifies a multimedia path whose active publication
is operationally expected to have at least one reader.

The policy does not determine whether a publisher exists, count readers,
maintain temporal state or raise alarms.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True, slots=True)
class CriticalPathPolicy:
    """Operational reader expectation for one critical multimedia path."""

    path: str
    enabled: bool = True
    no_readers_grace_period: timedelta = timedelta(
        seconds=15
    )
    unavailable_grace_period: timedelta = timedelta(
        seconds=15
    )

    def __post_init__(self) -> None:
        if not isinstance(self.path, str):
            raise TypeError(
                "path must be a string"
            )

        normalized_path = self.path.strip()

        if not normalized_path:
            raise ValueError(
                "path must not be empty"
            )

        object.__setattr__(
            self,
            "path",
            normalized_path,
        )

        if not isinstance(self.enabled, bool):
            raise TypeError(
                "enabled must be a bool"
            )

        if not isinstance(
            self.no_readers_grace_period,
            timedelta,
        ):
            raise TypeError(
                "no_readers_grace_period must be a timedelta"
            )

        if (
            self.no_readers_grace_period
            < timedelta(0)
        ):
            raise ValueError(
                "no_readers_grace_period must not be negative"
            )

        if not isinstance(
            self.unavailable_grace_period,
            timedelta,
        ):
            raise TypeError(
                "unavailable_grace_period must be a timedelta"
            )

        if (
            self.unavailable_grace_period
            < timedelta(0)
        ):
            raise ValueError(
                "unavailable_grace_period must not be negative"
            )
