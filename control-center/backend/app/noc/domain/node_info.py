"""Execution environment information for a NodeInstance.

ENG-013B — Node SDK
NCS reference: 10-NODE-INFO.md
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Mapping

from app.noc.domain.node_instance import NodeInstanceId


@dataclass(frozen=True, slots=True)
class NodeInfo:
    """Describes where and how a NodeInstance is executing.

    NodeInfo contains execution-environment information only.
    It does not represent logical identity, runtime state, health,
    metrics, alarms, events or availability.
    """

    instance_id: NodeInstanceId
    hostname: str
    platform: str
    operating_system: str
    architecture: str
    runtime: str
    boot_time: datetime

    fqdn: str | None = None
    location: str | None = None
    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        """Validate NodeInfo invariants."""
        if not isinstance(self.instance_id, NodeInstanceId):
            raise TypeError(
                "NodeInfo.instance_id must be a NodeInstanceId"
            )

        object.__setattr__(
            self,
            "hostname",
            self._normalize_required(
                self.hostname,
                "hostname",
            ),
        )

        object.__setattr__(
            self,
            "platform",
            self._normalize_required(
                self.platform,
                "platform",
            ),
        )

        object.__setattr__(
            self,
            "operating_system",
            self._normalize_required(
                self.operating_system,
                "operating_system",
            ),
        )

        object.__setattr__(
            self,
            "architecture",
            self._normalize_required(
                self.architecture,
                "architecture",
            ),
        )

        object.__setattr__(
            self,
            "runtime",
            self._normalize_required(
                self.runtime,
                "runtime",
            ),
        )

        object.__setattr__(
            self,
            "fqdn",
            self._normalize_optional(
                self.fqdn,
                "fqdn",
            ),
        )

        object.__setattr__(
            self,
            "location",
            self._normalize_optional(
                self.location,
                "location",
            ),
        )

        if not isinstance(self.boot_time, datetime):
            raise TypeError(
                "NodeInfo.boot_time must be a datetime"
            )

        if self.boot_time.tzinfo is None:
            raise ValueError(
                "NodeInfo.boot_time must be timezone-aware and UTC"
            )

        offset = self.boot_time.utcoffset()

        if offset is None or offset != timedelta(0):
            raise ValueError(
                "NodeInfo.boot_time must be expressed in UTC"
            )

        if self.metadata is not None:
            normalized_metadata: dict[str, str] = {}

            for key, value in self.metadata.items():
                if not isinstance(key, str):
                    raise TypeError(
                        "NodeInfo.metadata keys must be strings"
                    )

                if not isinstance(value, str):
                    raise TypeError(
                        "NodeInfo.metadata values must be strings"
                    )

                normalized_key = key.strip()
                normalized_value = value.strip()

                if not normalized_key:
                    raise ValueError(
                        "NodeInfo.metadata keys must not be empty"
                    )

                normalized_metadata[normalized_key] = normalized_value

            object.__setattr__(
                self,
                "metadata",
                normalized_metadata,
            )

    @property
    def uptime(self) -> timedelta:
        """Return the current execution uptime."""
        now = datetime.now(timezone.utc)
        uptime = now - self.boot_time

        if uptime < timedelta(0):
            return timedelta(0)

        return uptime

    @staticmethod
    def _normalize_required(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"NodeInfo.{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"NodeInfo.{field_name} must not be empty"
            )

        return normalized

    @staticmethod
    def _normalize_optional(
        value: str | None,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(
                f"NodeInfo.{field_name} must be a string or None"
            )

        normalized = value.strip()

        return normalized or None

    def __str__(self) -> str:
        """Return a human-readable execution identity."""
        return self.hostname
