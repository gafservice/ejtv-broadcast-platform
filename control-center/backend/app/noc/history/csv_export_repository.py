"""Port for publishing derived NOC history CSV exports.

ENG-013B — Operational History.

CSV exports are derived representations of durable operational history.
They are not authorities for operational state, historical persistence,
evidence sealing, retention, or backup.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class CsvExportResult:
    """Identity of one published CSV export."""

    path: Path
    events_file: Path
    alarm_transitions_file: Path

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            raise TypeError(
                "path must be a Path"
            )

        if not isinstance(self.events_file, Path):
            raise TypeError(
                "events_file must be a Path"
            )

        if not isinstance(
            self.alarm_transitions_file,
            Path,
        ):
            raise TypeError(
                "alarm_transitions_file must be a Path"
            )


@runtime_checkable
class CsvExportRepository(Protocol):
    """Persistence boundary for derived CSV history exports."""

    def publish(
        self,
        *,
        destination: Path,
        events_csv: str,
        alarm_transitions_csv: str,
    ) -> CsvExportResult:
        """Publish one derived CSV export without replacing an existing one."""
        ...
