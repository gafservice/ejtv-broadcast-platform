"""Presentation models for the INCOMING terminal dashboard view."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.streaming.health import HealthStatus


@dataclass(frozen=True, slots=True)
class IncomingRowData:
    """Presentation data for one incoming media path."""

    path_name: str
    source: str
    status: str
    bitrate_receive_mbps: float | None
    health_status: HealthStatus | None
    protocol: str | None = None
    remote_address: str | None = None
    health_reason: str | None = None
    health_since: datetime | None = None


@dataclass(frozen=True, slots=True)
class IncomingPanelData:
    """Immutable collection of incoming-path presentation rows."""

    rows: tuple[IncomingRowData, ...] = ()
    reference_at: datetime | None = None
