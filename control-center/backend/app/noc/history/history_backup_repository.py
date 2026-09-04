"""Port for consistent durable NOC history backups.

ENG-013B — Operational History

A history backup is a consistent standalone copy of the durable SQLite
operational-history database.

Coverage is expressed as an explicit UTC day boundary. It does not mean
that a historical row exists exactly at that boundary. Instead, it
declares the exclusive upper bound of managed durable history protected
by the backup.

This port does not decide backup cadence, retention eligibility, or
runtime ownership.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class HistoryBackupResult:
    """Identity and coverage metadata for one published backup."""

    path: Path
    created_at: datetime
    sha256: str
    covered_through: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            raise TypeError(
                "path must be a Path"
            )

        self._validate_utc_datetime(
            self.created_at,
            field_name="created_at",
        )

        if not isinstance(self.sha256, str):
            raise TypeError(
                "sha256 must be a str"
            )

        if len(self.sha256) != 64:
            raise ValueError(
                "sha256 must contain 64 hexadecimal characters"
            )

        try:
            int(self.sha256, 16)
        except ValueError as exc:
            raise ValueError(
                "sha256 must contain 64 hexadecimal characters"
            ) from exc

        self._validate_utc_datetime(
            self.covered_through,
            field_name="covered_through",
        )

        midnight = datetime.combine(
            self.covered_through.date(),
            time.min,
            tzinfo=timezone.utc,
        )

        if self.covered_through != midnight:
            raise ValueError(
                "covered_through must be aligned "
                "to a UTC day boundary"
            )

        if self.covered_through > self.created_at:
            raise ValueError(
                "covered_through must not be later "
                "than created_at"
            )

    @staticmethod
    def _validate_utc_datetime(
        value: datetime,
        *,
        field_name: str,
    ) -> None:
        if not isinstance(value, datetime):
            raise TypeError(
                f"{field_name} must be a datetime"
            )

        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                f"{field_name} must be timezone-aware"
            )

        if value.utcoffset().total_seconds() != 0:
            raise ValueError(
                f"{field_name} must be expressed in UTC"
            )


@runtime_checkable
class HistoryBackupRepository(Protocol):
    """Persistence boundary for consistent SQLite history backups."""

    def create_backup(
        self,
        *,
        destination: Path,
        created_at: datetime,
        covered_through: datetime,
    ) -> HistoryBackupResult:
        """Create and publish one consistent standalone backup."""
        ...
