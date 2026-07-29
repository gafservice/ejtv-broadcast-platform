"""Domain contract for identity and access audit records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from app.domain.identity.entities import AuthenticatedIdentity


@runtime_checkable
class AuditRepository(Protocol):
    """Contract for recording identity and access security events.

    Storage engines, log formats, observability platforms and transport
    mechanisms belong to the infrastructure layer.
    """

    def record(
        self,
        event_type: str,
        identity: AuthenticatedIdentity | None,
        details: Mapping[str, str] | None = None,
    ) -> None:
        """Record an identity or access-related audit event."""
        ...
