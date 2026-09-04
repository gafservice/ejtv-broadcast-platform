"""Durable metadata for immutable NOC SQLite history backups.

ENG-013B — Operational History

The metadata sidecar is the logical commit marker for one published
SQLite backup.

A database file without valid metadata may still be a recoverable
snapshot, but it is not eligible to prove retention coverage.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any


class HistoryBackupMetadataError(RuntimeError):
    """Raised when backup metadata is invalid or inconsistent."""


@dataclass(frozen=True, slots=True)
class HistoryBackupMetadata:
    """Immutable verification metadata for one SQLite backup."""

    FORMAT_VERSION = 1

    database_file: str
    created_at: datetime
    covered_through: datetime
    schema_version: int
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(
            self.database_file,
            str,
        ):
            raise TypeError(
                "database_file must be a str"
            )

        if (
            not self.database_file
            or Path(self.database_file).name
            != self.database_file
        ):
            raise ValueError(
                "database_file must be a basename"
            )

        self._validate_utc_datetime(
            self.created_at,
            field_name="created_at",
        )

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

        if not isinstance(
            self.schema_version,
            int,
        ):
            raise TypeError(
                "schema_version must be an int"
            )

        if self.schema_version < 1:
            raise ValueError(
                "schema_version must be positive"
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

    @property
    def metadata_filename(self) -> str:
        return (
            f"{self.database_file}.metadata.json"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": self.FORMAT_VERSION,
            "database_file": self.database_file,
            "created_at": self.created_at.isoformat(
                timespec="microseconds"
            ),
            "covered_through": (
                self.covered_through.isoformat(
                    timespec="microseconds"
                )
            ),
            "schema_version": self.schema_version,
            "sha256": self.sha256,
        }

    def to_json(self) -> str:
        return (
            json.dumps(
                self.to_dict(),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            + "\n"
        )

    @classmethod
    def from_json(
        cls,
        value: str,
    ) -> HistoryBackupMetadata:
        if not isinstance(value, str):
            raise TypeError(
                "value must be a str"
            )

        try:
            payload = json.loads(value)
        except json.JSONDecodeError as exc:
            raise HistoryBackupMetadataError(
                "backup metadata is not valid JSON"
            ) from exc

        if not isinstance(payload, dict):
            raise HistoryBackupMetadataError(
                "backup metadata must be a JSON object"
            )

        expected_keys = {
            "format_version",
            "database_file",
            "created_at",
            "covered_through",
            "schema_version",
            "sha256",
        }

        if set(payload) != expected_keys:
            raise HistoryBackupMetadataError(
                "backup metadata fields are invalid"
            )

        if (
            payload["format_version"]
            != cls.FORMAT_VERSION
        ):
            raise HistoryBackupMetadataError(
                "unsupported backup metadata format"
            )

        try:
            created_at = datetime.fromisoformat(
                payload["created_at"]
            )
            covered_through = datetime.fromisoformat(
                payload["covered_through"]
            )
        except (TypeError, ValueError) as exc:
            raise HistoryBackupMetadataError(
                "backup metadata timestamps are invalid"
            ) from exc

        try:
            return cls(
                database_file=payload["database_file"],
                created_at=created_at,
                covered_through=covered_through,
                schema_version=payload["schema_version"],
                sha256=payload["sha256"],
            )
        except (TypeError, ValueError) as exc:
            raise HistoryBackupMetadataError(
                "backup metadata values are invalid"
            ) from exc

    def publish(
        self,
        directory: Path,
    ) -> Path:
        if not isinstance(directory, Path):
            raise TypeError(
                "directory must be a Path"
            )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = (
            directory / self.metadata_filename
        )

        if destination.exists():
            raise FileExistsError(
                f"backup metadata already exists: "
                f"{destination}"
            )

        temporary = (
            directory
            / (
                f".{self.metadata_filename}."
                f"{uuid.uuid4().hex}.tmp"
            )
        )

        try:
            with temporary.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as handle:
                handle.write(
                    self.to_json()
                )
                handle.flush()
                os.fsync(handle.fileno())

            try:
                os.link(
                    temporary,
                    destination,
                )
            except FileExistsError:
                raise FileExistsError(
                    f"backup metadata already exists: "
                    f"{destination}"
                ) from None

            temporary.unlink()

            self._fsync_directory(
                directory
            )

            return destination
        finally:
            temporary.unlink(
                missing_ok=True
            )

    @classmethod
    def verify(
        cls,
        metadata_path: Path,
    ) -> bool:
        if not isinstance(
            metadata_path,
            Path,
        ):
            raise TypeError(
                "metadata_path must be a Path"
            )

        if not metadata_path.is_file():
            return False

        try:
            metadata = cls.from_json(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            UnicodeError,
            HistoryBackupMetadataError,
        ):
            return False

        database_path = (
            metadata_path.parent
            / metadata.database_file
        )

        if not database_path.is_file():
            return False

        try:
            actual_sha256 = (
                cls._sha256_file(
                    database_path
                )
            )

            actual_schema_version = (
                cls._read_schema_version(
                    database_path
                )
            )
        except (
            OSError,
            sqlite3.Error,
            ValueError,
        ):
            return False

        return (
            actual_sha256
            == metadata.sha256
            and actual_schema_version
            == metadata.schema_version
        )

    @staticmethod
    def _read_schema_version(
        path: Path,
    ) -> int:
        connection = sqlite3.connect(
            f"file:{path}?mode=ro",
            uri=True,
            timeout=5.0,
        )

        try:
            rows = connection.execute(
                """
                SELECT version
                FROM schema_version
                """
            ).fetchall()
        finally:
            connection.close()

        if len(rows) != 1:
            raise ValueError(
                "backup schema_version table "
                "must contain exactly one row"
            )

        version = rows[0][0]

        if (
            not isinstance(version, int)
            or isinstance(version, bool)
            or version < 1
        ):
            raise ValueError(
                "backup schema version is invalid"
            )

        return version

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
