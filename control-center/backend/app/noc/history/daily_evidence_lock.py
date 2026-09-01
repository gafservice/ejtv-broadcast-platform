"""Process-safe locking for one UTC evidence day.

ENG-013B — persistent operational history.

All writers and sealers for the same UTC evidence directory coordinate
through one advisory filesystem lock.  The lock file is intentionally
persistent and is not itself evidence.
"""

from __future__ import annotations

import fcntl
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Iterator


class DailyEvidenceLock:
    """Coordinate evidence operations for one UTC calendar day."""

    LOCK_FILENAME = ".evidence.lock"

    def __init__(
        self,
        root_path: str | Path,
    ) -> None:
        self._root_path = Path(root_path)

    @property
    def root_path(self) -> Path:
        return self._root_path

    def day_directory(
        self,
        day: date,
    ) -> Path:
        if not isinstance(day, date):
            raise TypeError(
                "day must be a date"
            )

        return (
            self._root_path
            / f"{day.year:04d}"
            / f"{day.month:02d}"
            / f"{day.day:02d}"
        )

    @contextmanager
    def exclusive(
        self,
        day: date,
    ) -> Iterator[Path]:
        """Hold the process-wide exclusive lock for one evidence day."""

        directory = self.day_directory(day)

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        lock_path = (
            directory
            / self.LOCK_FILENAME
        )

        with lock_path.open(
            "a+",
            encoding="utf-8",
        ) as handle:
            fcntl.flock(
                handle.fileno(),
                fcntl.LOCK_EX,
            )

            try:
                yield directory
            finally:
                fcntl.flock(
                    handle.fileno(),
                    fcntl.LOCK_UN,
                )
