"""Port for immutable daily NOC evidence backups.

ENG-013B — Operational History

An evidence backup preserves one UTC day of already sealed primary
historical evidence.

The backup contains the evidence artifacts themselves; it does not
reconstruct evidence from SQLite, seal open days, or decide backup
cadence and eligibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class EvidenceBackupResult:
    """Identity of one published daily evidence backup."""

    path: Path
    day: date

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            raise TypeError(
                "path must be a Path"
            )

        if not isinstance(self.day, date):
            raise TypeError(
                "day must be a date"
            )


@runtime_checkable
class EvidenceBackupRepository(Protocol):
    """Persistence boundary for immutable daily evidence backups."""

    def backup_day(
        self,
        *,
        day: date,
        destination: Path,
    ) -> EvidenceBackupResult:
        """Publish one immutable backup of a sealed UTC evidence day."""
        ...
