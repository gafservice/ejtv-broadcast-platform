"""Current-state projection for canonical Signal Health.

This module defines only the immutable current-state value and its
repository port. Persistence belongs to an infrastructure adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from app.domain.streaming.signal_health import SignalHealth


@dataclass(frozen=True, slots=True)
class SignalHealthCurrentState:
    """Latest known canonical Signal Health for one signal identity."""

    profile_id: str
    service_id: str
    path_name: str
    observed_at: datetime
    health: SignalHealth

    def __post_init__(self) -> None:
        profile_id = self._normalize_identity(
            self.profile_id,
            "profile_id",
        )
        service_id = self._normalize_identity(
            self.service_id,
            "service_id",
        )
        path_name = self._normalize_identity(
            self.path_name,
            "path_name",
        )

        if not isinstance(self.observed_at, datetime):
            raise TypeError("observed_at must be a datetime")

        if (
            self.observed_at.tzinfo is None
            or self.observed_at.utcoffset() is None
        ):
            raise ValueError("observed_at must be timezone-aware")

        if not isinstance(self.health, SignalHealth):
            raise TypeError("health must be a SignalHealth")

        health_identity = (
            self.health.profile_id,
            self.health.service_id,
            self.health.path_name,
        )
        state_identity = (
            profile_id,
            service_id,
            path_name,
        )

        if health_identity != state_identity:
            raise ValueError(
                "current-state identity must match SignalHealth identity"
            )

        object.__setattr__(self, "profile_id", profile_id)
        object.__setattr__(self, "service_id", service_id)
        object.__setattr__(self, "path_name", path_name)


    @staticmethod
    def _normalize_identity(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be blank"
            )

        return normalized


@runtime_checkable
class SignalHealthCurrentStateRepository(Protocol):
    """Storage-independent port for latest Signal Health state."""

    def save(
        self,
        *,
        state: SignalHealthCurrentState,
    ) -> None:
        """Create or replace the latest state for its identity."""
        ...

    def latest(
        self,
        *,
        profile_id: str,
        service_id: str,
        path_name: str,
    ) -> SignalHealthCurrentState | None:
        """Return the latest known state for one signal identity."""
        ...
