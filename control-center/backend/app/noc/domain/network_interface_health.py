"""Operational health evaluation for a network interface.

ENG-013B — Node SDK

This model represents the current health evaluation of one network
interface. It does not create events or alarms and does not define
alarm lifecycle behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.noc.domain.node_health import NodeHealthState


@dataclass(frozen=True, slots=True)
class NetworkInterfaceHealth:
    """Current operational health of one network interface."""

    interface: str
    state: NodeHealthState
    observed_at: datetime
    reason: str

    carrier_ok: bool | None = None
    traffic_ok: bool | None = None

    error_rate: float | None = None
    drop_rate: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.interface, str):
            raise TypeError(
                "interface must be a string"
            )

        interface = self.interface.strip()

        if not interface:
            raise ValueError(
                "interface must not be empty"
            )

        object.__setattr__(
            self,
            "interface",
            interface,
        )

        if not isinstance(self.state, NodeHealthState):
            raise TypeError(
                "state must be a NodeHealthState"
            )

        if not isinstance(self.observed_at, datetime):
            raise TypeError(
                "observed_at must be a datetime"
            )

        if self.observed_at.tzinfo is None:
            raise ValueError(
                "observed_at must be timezone-aware and UTC"
            )

        offset = self.observed_at.utcoffset()

        if offset is None or offset != timedelta(0):
            raise ValueError(
                "observed_at must be expressed in UTC"
            )

        if not isinstance(self.reason, str):
            raise TypeError(
                "reason must be a string"
            )

        reason = self.reason.strip()

        if not reason:
            raise ValueError(
                "reason must not be empty"
            )

        object.__setattr__(
            self,
            "reason",
            reason,
        )

        for name in (
            "carrier_ok",
            "traffic_ok",
        ):
            value = getattr(self, name)

            if value is not None and not isinstance(value, bool):
                raise TypeError(
                    f"{name} must be a bool or None"
                )

        for name in (
            "error_rate",
            "drop_rate",
        ):
            value = getattr(self, name)

            if value is None:
                continue

            if isinstance(value, bool) or not isinstance(
                value,
                (int, float),
            ):
                raise TypeError(
                    f"{name} must be numeric or None"
                )

            if value < 0:
                raise ValueError(
                    f"{name} must not be negative"
                )

            object.__setattr__(
                self,
                name,
                float(value),
            )

    @property
    def is_healthy(self) -> bool:
        return self.state is NodeHealthState.HEALTHY

    @property
    def requires_attention(self) -> bool:
        return self.state in {
            NodeHealthState.WARNING,
            NodeHealthState.DEGRADED,
            NodeHealthState.CRITICAL,
        }
