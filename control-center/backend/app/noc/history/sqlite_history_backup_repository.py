"""SQLite implementation of consistent NOC history backups.

ENG-013B — Operational History

The source database may be active in WAL mode. SQLite's Backup API is
used to obtain a transactionally consistent standalone database image.

Publication sequence:

1. backup into a temporary file beside the final destination;
2. verify the temporary database with PRAGMA integrity_check;
3. fsync the database file;
4. calculate SHA-256;
5. atomically publish the final immutable backup.

This adapter does not decide backup cadence or retention policy.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from app.noc.history.history_backup_repository import (
    HistoryBackupRepository,
    HistoryBackupResult,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)


class HistoryBackupIntegrityError(RuntimeError):
    """Raised when a newly created SQLite backup fails verification."""


class SQLiteHistoryBackupRepository:
    """Create consistent standalone backups through SQLite Backup API."""

    _COPY_CHUNK_SIZE = 1024 * 1024

    def __init__(
        self,
        database: SQLiteHistoryDatabase,
    ) -> None:
        if not isinstance(
            database,
            SQLiteHistoryDatabase,
        ):
            raise TypeError(
                "database must be a SQLiteHistoryDatabase"
            )

        self._database = database
        self._database.initialize()

    def create_backup(
        self,
        *,
        destination: Path,
        created_at: datetime,
        covered_through: datetime,
    ) -> HistoryBackupResult:
        self._validate_destination(destination)
        self._validate_created_at(created_at)
        self._validate_covered_through(
            covered_through,
            created_at=created_at,
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if destination.exists():
            raise FileExistsError(
                f"backup destination already exists: {destination}"
            )

        temporary = destination.with_name(
            f".{destination.name}.{uuid.uuid4().hex}.tmp"
        )

        try:
            self._create_consistent_copy(
                temporary
            )

            self._verify_integrity(
                temporary
            )

            self._fsync_file(
                temporary
            )

            sha256 = self._sha256(
                temporary
            )

            self._publish_without_overwrite(
                temporary=temporary,
                destination=destination,
            )

            self._fsync_directory(
                destination.parent
            )

            return HistoryBackupResult(
                path=destination,
                created_at=created_at,
                sha256=sha256,
                covered_through=covered_through,
            )
        except Exception:
            try:
                temporary.unlink(
                    missing_ok=True
                )
            except OSError:
                pass

            raise

    def _create_consistent_copy(
        self,
        destination: Path,
    ) -> None:
        source_connection = self._database.connect()

        try:
            destination_connection = sqlite3.connect(
                destination,
                timeout=5.0,
            )

            try:
                source_connection.backup(
                    destination_connection
                )
            finally:
                destination_connection.close()
        finally:
            source_connection.close()

    @staticmethod
    def _verify_integrity(
        path: Path,
    ) -> None:
        connection = sqlite3.connect(
            f"file:{path}?mode=ro",
            uri=True,
            timeout=5.0,
        )

        try:
            rows = connection.execute(
                "PRAGMA integrity_check"
            ).fetchall()
        finally:
            connection.close()

        messages = tuple(
            str(row[0])
            for row in rows
        )

        if messages != ("ok",):
            detail = "; ".join(messages)

            raise HistoryBackupIntegrityError(
                "SQLite backup integrity check failed"
                + (
                    f": {detail}"
                    if detail
                    else ""
                )
            )

    @classmethod
    def _sha256(
        cls,
        path: Path,
    ) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as file_handle:
            while True:
                chunk = file_handle.read(
                    cls._COPY_CHUNK_SIZE
                )

                if not chunk:
                    break

                digest.update(chunk)

        return digest.hexdigest()

    @staticmethod
    def _fsync_file(
        path: Path,
    ) -> None:
        with path.open("rb") as file_handle:
            os.fsync(
                file_handle.fileno()
            )

    @staticmethod
    def _publish_without_overwrite(
        *,
        temporary: Path,
        destination: Path,
    ) -> None:
        try:
            os.link(
                temporary,
                destination,
            )
        except FileExistsError:
            raise FileExistsError(
                f"backup destination already exists: {destination}"
            ) from None

        temporary.unlink()

    @staticmethod
    def _fsync_directory(
        path: Path,
    ) -> None:
        directory_fd = os.open(
            path,
            os.O_RDONLY,
        )

        try:
            os.fsync(
                directory_fd
            )
        finally:
            os.close(
                directory_fd
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
    def _validate_covered_through(
        covered_through: datetime,
        *,
        created_at: datetime,
    ) -> None:
        if not isinstance(
            covered_through,
            datetime,
        ):
            raise TypeError(
                "covered_through must be a datetime"
            )

        if (
            covered_through.tzinfo is None
            or covered_through.utcoffset() is None
        ):
            raise ValueError(
                "covered_through must be timezone-aware"
            )

        if (
            covered_through
            .utcoffset()
            .total_seconds()
            != 0
        ):
            raise ValueError(
                "covered_through must be expressed in UTC"
            )

        if (
            covered_through.hour != 0
            or covered_through.minute != 0
            or covered_through.second != 0
            or covered_through.microsecond != 0
        ):
            raise ValueError(
                "covered_through must be aligned "
                "to a UTC day boundary"
            )

        if covered_through > created_at:
            raise ValueError(
                "covered_through must not be later "
                "than created_at"
            )

    @staticmethod
    def _validate_created_at(
        created_at: datetime,
    ) -> None:
        if not isinstance(
            created_at,
            datetime,
        ):
            raise TypeError(
                "created_at must be a datetime"
            )

        if (
            created_at.tzinfo is None
            or created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )

        if (
            created_at
            .utcoffset()
            .total_seconds()
            != 0
        ):
            raise ValueError(
                "created_at must be expressed in UTC"
            )
