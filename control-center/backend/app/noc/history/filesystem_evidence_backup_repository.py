"""Filesystem backup adapter for sealed daily NOC evidence.

ENG-013B — Operational History

One backup is an immutable directory containing exactly the primary
evidence artifacts of one already sealed UTC day.

The source is never modified or reconstructed.  Open, incomplete, or
tampered evidence fails closed.
"""

from __future__ import annotations

import ctypes
import errno
import hashlib
import os
import shutil
import uuid
from datetime import date
from pathlib import Path

from app.noc.history.daily_evidence_lock import DailyEvidenceLock
from app.noc.history.evidence_backup_repository import (
    EvidenceBackupRepository,
    EvidenceBackupResult,
)


class EvidenceBackupError(RuntimeError):
    """Raised when daily evidence cannot be safely backed up."""


class FilesystemEvidenceBackupRepository(EvidenceBackupRepository):
    """Publish immutable verified copies of sealed daily evidence."""

    MANIFEST_FILENAME = "manifest.sha256"

    EVIDENCE_FILENAMES = (
        "alarm_transitions.jsonl",
        "events.jsonl",
    )

    def __init__(
        self,
        source_root: str | Path,
    ) -> None:
        self._source_root = Path(source_root)
        self._daily_lock = DailyEvidenceLock(
            self._source_root
        )

    def backup_day(
        self,
        *,
        day: date,
        destination: Path,
    ) -> EvidenceBackupResult:
        if not isinstance(day, date):
            raise TypeError(
                "day must be a date"
            )

        if not isinstance(destination, Path):
            raise TypeError(
                "destination must be a Path"
            )

        final_directory = (
            destination
            / f"{day.year:04d}"
            / f"{day.month:02d}"
            / f"{day.day:02d}"
        )

        if final_directory.exists():
            raise FileExistsError(
                "evidence backup already exists: "
                f"{final_directory}"
            )

        parent = final_directory.parent
        parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = (
            parent
            / (
                f".{day.day:02d}."
                f"{uuid.uuid4().hex}.tmp"
            )
        )

        published = False

        try:
            with self._daily_lock.exclusive(
                day
            ) as source_directory:
                manifest = self._read_valid_manifest(
                    source_directory
                )

                temporary.mkdir()

                for filename in self.EVIDENCE_FILENAMES:
                    self._copy_file(
                        source_directory / filename,
                        temporary / filename,
                    )

                self._copy_file(
                    source_directory / self.MANIFEST_FILENAME,
                    temporary / self.MANIFEST_FILENAME,
                )

                self._fsync_directory(
                    temporary
                )

                if not self._verify_directory(
                    temporary,
                    manifest=manifest,
                ):
                    raise EvidenceBackupError(
                        "copied evidence does not match manifest"
                    )

                self._publish_without_overwrite(
                    temporary=temporary,
                    destination=final_directory,
                )

                published = True

            self._fsync_directory(
                parent
            )

            return EvidenceBackupResult(
                path=final_directory,
                day=day,
            )
        finally:
            if not published and temporary.exists():
                shutil.rmtree(
                    temporary
                )

    def verify_backup(
        self,
        *,
        day: date,
        destination: Path,
    ) -> bool:
        """Verify one previously published daily evidence backup."""

        if not isinstance(day, date):
            raise TypeError(
                "day must be a date"
            )

        if not isinstance(destination, Path):
            raise TypeError(
                "destination must be a Path"
            )

        directory = (
            destination
            / f"{day.year:04d}"
            / f"{day.month:02d}"
            / f"{day.day:02d}"
        )

        if not directory.is_dir():
            return False

        try:
            manifest = (
                directory
                / self.MANIFEST_FILENAME
            ).read_text(
                encoding="utf-8"
            )
        except (OSError, UnicodeError):
            return False

        return self._verify_directory(
            directory,
            manifest=manifest,
        )

    def _read_valid_manifest(
        self,
        directory: Path,
    ) -> str:
        manifest_path = (
            directory
            / self.MANIFEST_FILENAME
        )

        if not manifest_path.is_file():
            raise EvidenceBackupError(
                "evidence day is not sealed"
            )

        try:
            manifest = manifest_path.read_text(
                encoding="utf-8"
            )
        except (OSError, UnicodeError) as exc:
            raise EvidenceBackupError(
                "evidence manifest cannot be read"
            ) from exc

        if not self._verify_directory(
            directory,
            manifest=manifest,
        ):
            raise EvidenceBackupError(
                "sealed evidence does not match manifest"
            )

        return manifest

    def _verify_directory(
        self,
        directory: Path,
        *,
        manifest: str,
    ) -> bool:
        try:
            expected = self._build_manifest(
                directory
            )
        except OSError:
            return False

        return manifest == expected

    def _build_manifest(
        self,
        directory: Path,
    ) -> str:
        lines: list[str] = []

        for filename in self.EVIDENCE_FILENAMES:
            path = directory / filename

            if not path.is_file():
                raise FileNotFoundError(
                    f"evidence file is missing: {filename}"
                )

            digest = self._sha256_file(
                path
            )

            lines.append(
                f"{digest}  {filename}"
            )

        return "\n".join(lines) + "\n"

    @staticmethod
    def _copy_file(
        source: Path,
        destination: Path,
    ) -> None:
        with source.open("rb") as source_handle:
            with destination.open("xb") as destination_handle:
                shutil.copyfileobj(
                    source_handle,
                    destination_handle,
                    length=1024 * 1024,
                )

                destination_handle.flush()
                os.fsync(
                    destination_handle.fileno()
                )

    @staticmethod
    def _publish_without_overwrite(
        *,
        temporary: Path,
        destination: Path,
    ) -> None:
        """Atomically publish one directory without replacement.

        Linux renameat2(RENAME_NOREPLACE) closes the TOCTOU window
        between checking destination existence and publication.
        """

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
                "atomic evidence publication requires "
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
                "evidence backup already exists: "
                f"{destination}"
            )

        raise OSError(
            error_number,
            os.strerror(error_number),
            destination,
        )

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
