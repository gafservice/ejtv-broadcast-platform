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
    alarm_count: int = 0
    alarm_severity: str | None = None
    transport_health_status: HealthStatus | None = None
    transport_source_type: str | None = None
    transport_ready: bool | None = None
    transport_available: bool | None = None
    transport_online: bool | None = None
    transport_available_since: datetime | None = None
    transport_online_since: datetime | None = None
    transport_received_bytes: int | None = None
    transport_inbound_frames_in_error: int | None = None
    transport_observed_at: datetime | None = None
    transport_health_since: datetime | None = None
    bitrate_average_mbps: float | None = None
    bitrate_minimum_mbps: float | None = None
    bitrate_maximum_mbps: float | None = None
    transport_source_id: str | None = None
    transport_observed_interruptions: int | None = None
    transport_observed_recoveries: int | None = None


@dataclass(frozen=True, slots=True)
class IncomingPanelData:
    """Immutable collection of incoming-path presentation rows."""

    rows: tuple[IncomingRowData, ...] = ()
    reference_at: datetime | None = None
