"""Port for publishing derived NOC history PDF exports.

ENG-013B — Operational History.

PDF exports are derived representations of durable operational history.
They are not authorities for operational state, historical persistence,
evidence sealing, retention, or backup.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class PdfExportResult:
    """Identity of one published PDF export."""

    path: Path
    report_file: Path

    def __post_init__(self) -> None:
        if not isinstance(
            self.path,
            Path,
        ):
            raise TypeError(
                "path must be a Path"
            )

        if not isinstance(
            self.report_file,
            Path,
        ):
            raise TypeError(
                "report_file must be a Path"
            )


@runtime_checkable
class PdfExportRepository(Protocol):
    """Persistence boundary for derived PDF history exports."""

    def publish(
        self,
        *,
        destination: Path,
        pdf_document: bytes,
    ) -> PdfExportResult:
        """Publish one derived PDF export without replacing an existing one."""

        ...
