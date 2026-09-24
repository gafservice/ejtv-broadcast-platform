"""Aggregate health for one logical multimedia signal.

ENG-013C — Signal Health Contract v1

Signal Health combines already-evaluated Media Health and Source
Transport Health.

This boundary deliberately does not inspect codecs, GOP, PCR, MPEG-TS,
packets, sessions, protocol metrics, or physical transport evidence.

Those concerns remain owned by their respective domains:

- Media Health owns evaluated media evidence.
- Source Transport Health owns the evaluated conclusion about the
  transport feeding the logical signal.
- Signal Health combines their operational conclusions without
  inventing or reinterpreting lower-level evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.streaming.source_transport_health import (
    SourceTransportHealth,
)
from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import MediaHealth


@dataclass(frozen=True, slots=True)
class SignalHealth:
    """Operational health of one logical multimedia signal."""

    profile_id: str
    service_id: str
    path_name: str | None
    media_status: HealthStatus
    transport_status: HealthStatus
    status: HealthStatus

    def __post_init__(self) -> None:
        profile_id = self.profile_id.strip()
        service_id = self.service_id.strip()

        if not profile_id:
            raise ValueError("profile_id must not be blank")

        if not service_id:
            raise ValueError("service_id must not be blank")

        path_name = self.path_name

        if path_name is not None:
            path_name = path_name.strip()

            if not path_name:
                raise ValueError(
                    "path_name must not be blank when provided"
                )

        for field_name in (
            "media_status",
            "transport_status",
            "status",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, HealthStatus):
                raise TypeError(
                    f"{field_name} must be a HealthStatus"
                )

        object.__setattr__(self, "profile_id", profile_id)
        object.__setattr__(self, "service_id", service_id)
        object.__setattr__(self, "path_name", path_name)


class SignalHealthEvaluator:
    """Combine Media Health and Source Transport Health for one logical signal."""

    def evaluate(
        self,
        *,
        transport_health: SourceTransportHealth,
        media_health: MediaHealth | None = None,
        profile_id: str | None = None,
        service_id: str | None = None,
        path_name: str | None = None,
        media_status: HealthStatus | None = None,
    ) -> SignalHealth:
        """Return aggregate Signal Health without inventing evidence."""

        if not isinstance(
            transport_health,
            SourceTransportHealth,
        ):
            raise TypeError(
                "transport_health must be a SourceTransportHealth"
            )

        explicit_media_status_mode = media_health is None

        if media_health is not None:
            if not isinstance(media_health, MediaHealth):
                raise TypeError(
                    "media_health must be a MediaHealth"
                )

            if any(
                value is not None
                for value in (
                    profile_id,
                    service_id,
                    path_name,
                    media_status,
                )
            ):
                raise ValueError(
                    "media_health cannot be combined with "
                    "explicit media identity or media_status"
                )

            effective_profile_id = media_health.profile_id
            effective_service_id = media_health.service_id
            effective_path_name = media_health.path_name
            effective_media_status = media_health.status

        else:
            if not isinstance(media_status, HealthStatus):
                raise TypeError(
                    "media_status must be a HealthStatus"
                )

            effective_profile_id = profile_id
            effective_service_id = service_id
            effective_path_name = path_name
            effective_media_status = media_status

        if effective_service_id != transport_health.service_id:
            raise ValueError(
                "media and transport service identities must match"
            )

        if (
            explicit_media_status_mode
            and effective_path_name != transport_health.path_name
        ):
            raise ValueError(
                "media and transport path identities must match"
            )

        status = self._resolve_status(
            effective_media_status,
            transport_health.status,
        )

        return SignalHealth(
            profile_id=effective_profile_id,
            service_id=effective_service_id,
            path_name=effective_path_name,
            media_status=effective_media_status,
            transport_status=transport_health.status,
            status=status,
        )

    @staticmethod
    def _resolve_status(
        media_status: HealthStatus,
        transport_status: HealthStatus,
    ) -> HealthStatus:
        """Resolve cross-domain health conservatively.

        Known negative evidence dominates.

        UNKNOWN prevents an aggregate HEALTHY conclusion when either
        domain lacks sufficient evidence, but UNKNOWN never hides a
        known DEGRADED or CRITICAL condition.
        """

        statuses = (
            media_status,
            transport_status,
        )

        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL

        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED

        if HealthStatus.UNKNOWN in statuses:
            return HealthStatus.UNKNOWN

        return HealthStatus.HEALTHY
