"""Filesystem adapter for derived NOC history CSV exports.

ENG-013B — Operational History.

One export is published as one immutable directory containing exactly:

- events.csv
- alarm_transitions.csv

CSV is a derived representation. This adapter does not query SQLite,
decide history ranges, seal evidence, perform retention, or own backup
policy.
"""

from __future__ import annotations

import ctypes
import errno
import os
import shutil
import uuid
from pathlib import Path

from app.noc.history.csv_export_repository import (
    CsvExportRepository,
    CsvExportResult,
)


class FilesystemCsvExportRepository(CsvExportRepository):
    """Atomically publish one pair of derived CSV history files."""

    EVENTS_FILENAME = "events.csv"
    ALARM_TRANSITIONS_FILENAME = "alarm_transitions.csv"

    def publish(
        self,
        *,
        destination: Path,
        events_csv: str,
        alarm_transitions_csv: str,
    ) -> CsvExportResult:
        self._validate_destination(
            destination
        )
        self._validate_csv_text(
            events_csv,
            name="events_csv",
        )
        self._validate_csv_text(
            alarm_transitions_csv,
            name="alarm_transitions_csv",
        )

        if destination.exists():
            raise FileExistsError(
                "CSV export destination already exists: "
                f"{destination}"
            )

        parent = destination.parent
        parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = parent / (
            f".{destination.name}."
            f"{uuid.uuid4().hex}.tmp"
        )

        published = False

        try:
            temporary.mkdir()

            events_file = (
                temporary
                / self.EVENTS_FILENAME
            )
            alarm_transitions_file = (
                temporary
                / self.ALARM_TRANSITIONS_FILENAME
            )

            self._write_text_file(
                events_file,
                events_csv,
            )
            self._write_text_file(
                alarm_transitions_file,
                alarm_transitions_csv,
            )

            self._fsync_directory(
                temporary
            )

            self._publish_without_overwrite(
                temporary=temporary,
                destination=destination,
            )

            published = True

            self._fsync_directory(
                parent
            )

            return CsvExportResult(
                path=destination,
                events_file=(
                    destination
                    / self.EVENTS_FILENAME
                ),
                alarm_transitions_file=(
                    destination
                    / self.ALARM_TRANSITIONS_FILENAME
                ),
            )
        finally:
            if (
                not published
                and temporary.exists()
            ):
                shutil.rmtree(
                    temporary
                )

    @staticmethod
    def _write_text_file(
        path: Path,
        content: str,
    ) -> None:
        with path.open(
            "x",
            encoding="utf-8",
            newline="",
        ) as handle:
            handle.write(
                content
            )
            handle.flush()
            os.fsync(
                handle.fileno()
            )

    @staticmethod
    def _publish_without_overwrite(
        *,
        temporary: Path,
        destination: Path,
    ) -> None:
        """Atomically publish a directory without replacement."""

        libc = ctypes.CDLL(
            None,
            use_errno=True,
        )

        renameat2 = getattr(
            libc,
            "renameat2",
            None,
        )

        if renameat2 is None:
            raise RuntimeError(
                "atomic CSV publication requires "
                "renameat2(RENAME_NOREPLACE)"
            )

        renameat2.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        renameat2.restype = ctypes.c_int

        at_fdcwd = -100
        rename_noreplace = 1

        result = renameat2(
            at_fdcwd,
            os.fsencode(temporary),
            at_fdcwd,
            os.fsencode(destination),
            rename_noreplace,
        )

        if result == 0:
            return

        error_number = ctypes.get_errno()

        if error_number in (
            errno.EEXIST,
            errno.ENOTEMPTY,
        ):
            raise FileExistsError(
                "CSV export destination already exists: "
                f"{destination}"
            )

        raise OSError(
            error_number,
            os.strerror(error_number),
            destination,
        )

    @staticmethod
    def _fsync_directory(
        directory: Path,
    ) -> None:
        descriptor = os.open(
            directory,
            os.O_RDONLY,
        )

        try:
            os.fsync(
                descriptor
            )
        finally:
            os.close(
                descriptor
            )

    @staticmethod
    def _validate_destination(
        destination: Path,
    ) -> None:
        if not isinstance(
            destination,
            Path,
        ):
            raise TypeError(
                "destination must be a Path"
            )

    @staticmethod
    def _validate_csv_text(
        value: str,
        *,
        name: str,
    ) -> None:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{name} must be a str"
            )
