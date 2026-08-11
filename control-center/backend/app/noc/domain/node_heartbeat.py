"""Heartbeat presence model for a NodeInstance.

ENG-013B — Node SDK
NCS reference: 19-NODE-HEARTBEAT.md
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from numbers import Integral

from app.noc.domain.node_instance import NodeInstanceId


@dataclass(frozen=True, slots=True)
class HeartbeatRecord:
    """Periodic proof of presence emitted by a NodeInstance."""

    heartbeat_id: str
    instance_id: NodeInstanceId
    sequence: int
    timestamp: datetime
    contract_version: str
    uptime: float
    checksum: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "heartbeat_id",
            self._normalize_required(
                self.heartbeat_id,
                "heartbeat_id",
            ),
        )

        object.__setattr__(
            self,
            "contract_version",
            self._normalize_required(
                self.contract_version,
                "contract_version",
            ),
        )

        if not isinstance(self.instance_id, NodeInstanceId):
            raise TypeError(
                "HeartbeatRecord.instance_id must be a NodeInstanceId"
            )

        if isinstance(self.sequence, bool) or not isinstance(
            self.sequence,
            Integral,
        ):
            raise TypeError(
                "HeartbeatRecord.sequence must be an integer"
            )

        if self.sequence < 0:
            raise ValueError(
                "HeartbeatRecord.sequence must not be negative"
            )

        if not isinstance(self.timestamp, datetime):
            raise TypeError(
                "HeartbeatRecord.timestamp must be a datetime"
            )

        if self.timestamp.tzinfo is None:
            raise ValueError(
                "HeartbeatRecord.timestamp must be timezone-aware and UTC"
            )

        offset = self.timestamp.utcoffset()

        if offset is None or offset != timedelta(0):
            raise ValueError(
                "HeartbeatRecord.timestamp must be expressed in UTC"
            )

        if isinstance(self.uptime, bool) or not isinstance(
            self.uptime,
            (int, float),
        ):
            raise TypeError(
                "HeartbeatRecord.uptime must be numeric"
            )

        if self.uptime < 0:
            raise ValueError(
                "HeartbeatRecord.uptime must not be negative"
            )

        if self.checksum is not None:
            object.__setattr__(
                self,
                "checksum",
                self._normalize_optional(
                    self.checksum,
                    "checksum",
                ),
            )

    @staticmethod
    def _normalize_required(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"HeartbeatRecord.{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"HeartbeatRecord.{field_name} must not be empty"
            )

        return normalized

    @staticmethod
    def _normalize_optional(
        value: str,
        field_name: str,
    ) -> str | None:
        if not isinstance(value, str):
            raise TypeError(
                f"HeartbeatRecord.{field_name} must be a string"
            )

        normalized = value.strip()

        return normalized or None

    def __str__(self) -> str:
        return (
            f"{self.instance_id} "
            f"seq={self.sequence}"
        )


@dataclass(frozen=True, slots=True)
class NodeHeartbeat:
    """Latest known heartbeat of a NodeInstance."""

    latest: HeartbeatRecord | None = None

    def __post_init__(self) -> None:
        if self.latest is not None and not isinstance(
            self.latest,
            HeartbeatRecord,
        ):
            raise TypeError(
                "NodeHeartbeat.latest must be a HeartbeatRecord or None"
            )

    @property
    def is_present(self) -> bool:
        """Return whether at least one heartbeat is known."""
        return self.latest is not None

    @property
    def sequence(self) -> int | None:
        if self.latest is None:
            return None

        return self.latest.sequence

    @property
    def timestamp(self) -> datetime | None:
        if self.latest is None:
            return None

        return self.latest.timestamp

    @property
    def uptime(self) -> float | None:
        if self.latest is None:
            return None

        return self.latest.uptime

    def belongs_to(
        self,
        instance_id: NodeInstanceId,
    ) -> bool:
        """Return whether the latest heartbeat belongs to an instance."""
        if not isinstance(instance_id, NodeInstanceId):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

        if self.latest is None:
            return False

        return self.latest.instance_id == instance_id
