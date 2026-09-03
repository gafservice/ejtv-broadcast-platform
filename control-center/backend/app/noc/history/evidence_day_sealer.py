"""Daily evidence sealing with SHA-256 manifests."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.noc.history.daily_evidence_lock import (
    DailyEvidenceLock,
)


class EvidenceSealConflictError(RuntimeError):
    """Raised when an existing manifest does not match evidence."""


@dataclass(frozen=True)
class EvidenceDaySealResult:
    """Result of sealing one evidence day."""

    day: date
    manifest_path: Path
    created: bool


class EvidenceDaySealer:
    """Seal one UTC evidence day with deterministic SHA-256 hashes."""

    MANIFEST_FILENAME = "manifest.sha256"

    EVIDENCE_FILENAMES = (
        "alarm_transitions.jsonl",
        "events.jsonl",
    )

    def __init__(
        self,
        root_path: str | Path,
    ) -> None:
        self._root_path = Path(root_path)
        self._daily_lock = DailyEvidenceLock(
            self._root_path
        )

    def assert_day_can_be_finalized(
        self,
        day: date,
    ) -> None:
        """Reject an existing invalid seal before finalization.

        An unsealed day is eligible for reconciliation and sealing.
        An already sealed day is eligible only when its manifest still
        matches the current primary evidence.
        """

        with self._daily_lock.exclusive(day) as directory:
            manifest_path = (
                directory
                / self.MANIFEST_FILENAME
            )

            if not manifest_path.exists():
                return

            current = manifest_path.read_text(
                encoding="utf-8"
            )

            expected = self._build_manifest(
                directory,
                require_existing=True,
            )

            if current != expected:
                raise EvidenceSealConflictError(
                    "existing manifest does not "
                    "match current evidence"
                )

    def seal_day(
        self,
        day: date,
    ) -> EvidenceDaySealResult:
        """Seal one UTC day.

        The manifest is written atomically while holding the day-wide
        process lock.
        """

        with self._daily_lock.exclusive(day) as directory:
            manifest_path = (
                directory
                / self.MANIFEST_FILENAME
            )

            if manifest_path.exists():
                current = manifest_path.read_text(
                    encoding="utf-8"
                )

                expected = self._build_manifest(
                    directory,
                    require_existing=True,
                )

                if current != expected:
                    raise EvidenceSealConflictError(
                        "existing manifest does not "
                        "match current evidence"
                    )

                return EvidenceDaySealResult(
                    day=day,
                    manifest_path=manifest_path,
                    created=False,
                )

            self._ensure_evidence_files(
                directory
            )

            expected = self._build_manifest(
                directory,
                require_existing=True,
            )

            temporary_path = (
                directory
                / f".{self.MANIFEST_FILENAME}.tmp"
            )

            try:
                with temporary_path.open(
                    "w",
                    encoding="utf-8",
                    newline="\n",
                ) as handle:
                    handle.write(expected)
                    handle.flush()
                    os.fsync(handle.fileno())

                os.replace(
                    temporary_path,
                    manifest_path,
                )

                self._fsync_directory(
                    directory
                )
            finally:
                if temporary_path.exists():
                    temporary_path.unlink()

            return EvidenceDaySealResult(
                day=day,
                manifest_path=manifest_path,
                created=True,
            )

    def verify_day(
        self,
        day: date,
    ) -> bool:
        """Return whether a sealed day matches its manifest."""

        with self._daily_lock.exclusive(day) as directory:
            manifest_path = (
                directory
                / self.MANIFEST_FILENAME
            )

            if not manifest_path.exists():
                return False

            current = manifest_path.read_text(
                encoding="utf-8"
            )

            try:
                expected = self._build_manifest(
                    directory,
                    require_existing=True,
                )
            except EvidenceSealConflictError:
                return False

            return current == expected

    def _ensure_evidence_files(
        self,
        directory: Path,
    ) -> None:
        """Create primary evidence files before first sealing."""

        created = False

        for filename in self.EVIDENCE_FILENAMES:
            path = directory / filename

            if path.exists():
                continue

            with path.open(
                "xb"
            ) as handle:
                handle.flush()
                os.fsync(handle.fileno())

            created = True

        if created:
            self._fsync_directory(
                directory
            )

    def _build_manifest(
        self,
        directory: Path,
        *,
        require_existing: bool,
    ) -> str:
        lines: list[str] = []

        for filename in self.EVIDENCE_FILENAMES:
            path = directory / filename

            if not path.exists():
                if require_existing:
                    raise EvidenceSealConflictError(
                        "sealed evidence file is missing: "
                        f"{filename}"
                    )

                continue

            digest = self._sha256_file(path)

            lines.append(
                f"{digest}  {filename}"
            )

        return "\n".join(lines) + "\n"

    @staticmethod
    def _sha256_file(
        path: Path,
    ) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as handle:
            while True:
                chunk = handle.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                digest.update(chunk)

        return digest.hexdigest()

    @staticmethod
    def _fsync_directory(
        directory: Path,
    ) -> None:
        descriptor = os.open(
            directory,
            os.O_RDONLY,
        )

        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
