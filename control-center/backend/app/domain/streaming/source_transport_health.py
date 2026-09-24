"""Health conclusion for the transport feeding one multimedia signal.

ENG-013C — Source Transport Health Contract v1

Source Transport Health represents an already-evaluated conclusion about
the transport that feeds one logical multimedia signal.

This domain object deliberately does not contain client/delivery session
identity, protocol-specific transport metrics, or media evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.streaming.health import HealthStatus


@dataclass(frozen=True, slots=True)
class SourceTransportHealth:
    """Health of the transport feeding one logical multimedia signal."""

    service_id: str
    path_name: str
    source_type: str
    status: HealthStatus

    def __post_init__(self) -> None:
        service_id = self.service_id.strip()
        path_name = self.path_name.strip()
        source_type = self.source_type.strip()

        if not service_id:
            raise ValueError(
                "service_id must not be blank"
            )

        if not path_name:
            raise ValueError(
                "path_name must not be blank"
            )

        if not source_type:
            raise ValueError(
                "source_type must not be blank"
            )

        if not isinstance(self.status, HealthStatus):
            raise TypeError(
                "status must be a HealthStatus"
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
        object.__setattr__(
            self,
            "source_type",
            source_type,
        )
