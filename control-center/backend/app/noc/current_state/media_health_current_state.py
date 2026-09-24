"""Shared current-state contract for stabilized Media Health.

ENG-013C — Media Health Current State

This module defines the latest known stabilized Media Health projection
for one configured media profile and the storage-independent repository
port used to publish and retrieve that projection.

Current state is distinct from immutable operational history.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from app.domain.streaming.media_health import MediaHealth


@dataclass(frozen=True, slots=True)
class MediaHealthCurrentState:
    """Latest stabilized Media Health projection for one media profile."""

    profile_id: str
    service_id: str
    path_name: str
    observed_at: datetime
    health: MediaHealth

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

        if not isinstance(self.health, MediaHealth):
            raise TypeError(
                "health must be a MediaHealth"
            )

        if (
            profile_id != self.health.profile_id
            or service_id != self.health.service_id
            or path_name != self.health.path_name
        ):
            raise ValueError(
                "current-state identity must match "
                "MediaHealth identity"
            )

        object.__setattr__(
            self,
            "profile_id",
            profile_id,
        )
        object.__setattr__(
            self,
            "service_id",
            service_id,
        )
        object.__setattr__(
            self,
            "path_name",
            path_name,
        )

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
class MediaHealthCurrentStateRepository(Protocol):
    """Storage-independent port for latest Media Health state."""

    def save(
        self,
        *,
        state: MediaHealthCurrentState,
    ) -> None:
        """Create or replace the latest state for its identity."""
        ...

    def latest(
        self,
        *,
        profile_id: str,
        service_id: str,
        path_name: str,
    ) -> MediaHealthCurrentState | None:
        """Return the latest known state for one media identity."""
        ...
