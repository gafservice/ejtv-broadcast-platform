"""Reconnect flapping policy for multimedia sessions.

ENG-013B — Node SDK

ReconnectFlappingPolicy defines the temporal thresholds used to classify
repeated multimedia reconnects as operational flapping.

The policy is transport-independent and applies to logical session
identities rather than concrete session_id values.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True, slots=True)
class ReconnectFlappingPolicy:
    """Temporal policy for reconnect flapping detection."""

    reconnect_timeout: timedelta = timedelta(seconds=10)
    window: timedelta = timedelta(seconds=60)
    threshold: int = 3

    def __post_init__(self) -> None:
        if not isinstance(
            self.reconnect_timeout,
            timedelta,
        ):
            raise TypeError(
                "reconnect_timeout must be a timedelta"
            )

        if self.reconnect_timeout <= timedelta(0):
            raise ValueError(
                "reconnect_timeout must be greater than zero"
            )

        if not isinstance(
            self.window,
            timedelta,
        ):
            raise TypeError(
                "window must be a timedelta"
            )

        if self.window <= timedelta(0):
            raise ValueError(
                "window must be greater than zero"
            )

        if self.reconnect_timeout > self.window:
            raise ValueError(
                "reconnect_timeout must not exceed window"
            )

        if not isinstance(self.threshold, int):
            raise TypeError(
                "threshold must be an int"
            )

        if isinstance(self.threshold, bool):
            raise TypeError(
                "threshold must be an int"
            )

        if self.threshold < 2:
            raise ValueError(
                "threshold must be at least 2"
            )
