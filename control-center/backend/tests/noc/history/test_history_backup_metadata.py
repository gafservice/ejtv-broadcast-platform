from __future__ import annotations

import hashlib
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.noc.history.history_backup_metadata import (
    HistoryBackupMetadata,
    HistoryBackupMetadataError,
)


CREATED_AT = datetime(
    2026,
    9,
    4,
    9,
    30,
    tzinfo=UTC,
)

COVERED_THROUGH = datetime(
    2026,
    9,
    4,
    0,
    0,
    tzinfo=UTC,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def _create_database(
    path: Path,
    *,
    schema_version: int = 3,
) -> None:
    connection = sqlite3.connect(path)

    try:
        connection.execute(
            """
            CREATE TABLE schema_version (
                version INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO schema_version(version)
            VALUES (?)
            """,
            (schema_version,),
        )
        connection.commit()
    finally:
        connection.close()


def _metadata(
    database_path: Path,
    *,
    schema_version: int = 3,
) -> HistoryBackupMetadata:
    return HistoryBackupMetadata(
        database_file=database_path.name,
        created_at=CREATED_AT,
        covered_through=COVERED_THROUGH,
        schema_version=schema_version,
        sha256=_sha256(database_path),
    )


def test_metadata_round_trip_is_canonical(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "history.sqlite3"
    )
    _create_database(database_path)

    metadata = _metadata(
        database_path
    )

    restored = (
        HistoryBackupMetadata.from_json(
            metadata.to_json()
        )
    )

    assert restored == metadata
    assert (
        restored.to_json()
        == metadata.to_json()
    )


def test_metadata_rejects_unknown_fields(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "history.sqlite3"
    )
    _create_database(database_path)

    value = _metadata(
        database_path
    ).to_json()

    value = value.replace(
        '"schema_version":3',
        '"extra":true,"schema_version":3',
    )

    with pytest.raises(
        HistoryBackupMetadataError,
        match="fields are invalid",
    ):
        HistoryBackupMetadata.from_json(
            value
        )


def test_publish_and_verify_metadata(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "history.sqlite3"
    )
    _create_database(database_path)

    metadata = _metadata(
        database_path
    )

    metadata_path = metadata.publish(
        tmp_path
    )

    assert metadata_path.is_file()

    assert (
        HistoryBackupMetadata.verify(
            metadata_path
        )
        is True
    )


def test_tampered_database_fails_verification(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "history.sqlite3"
    )
    _create_database(database_path)

    metadata = _metadata(
        database_path
    )

    metadata_path = metadata.publish(
        tmp_path
    )

    with database_path.open("ab") as handle:
        handle.write(b"tampered")

    assert (
        HistoryBackupMetadata.verify(
            metadata_path
        )
        is False
    )


def test_missing_database_fails_verification(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "history.sqlite3"
    )
    _create_database(database_path)

    metadata = _metadata(
        database_path
    )

    metadata_path = metadata.publish(
        tmp_path
    )

    database_path.unlink()

    assert (
        HistoryBackupMetadata.verify(
            metadata_path
        )
        is False
    )


def test_corrupt_metadata_fails_verification(
    tmp_path,
) -> None:
    metadata_path = (
        tmp_path
        / "history.sqlite3.metadata.json"
    )

    metadata_path.write_text(
        "{not-json}\n",
        encoding="utf-8",
    )

    assert (
        HistoryBackupMetadata.verify(
            metadata_path
        )
        is False
    )


def test_schema_version_mismatch_fails_verification(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "history.sqlite3"
    )
    _create_database(
        database_path,
        schema_version=3,
    )

    metadata = _metadata(
        database_path,
        schema_version=2,
    )

    metadata_path = metadata.publish(
        tmp_path
    )

    assert (
        HistoryBackupMetadata.verify(
            metadata_path
        )
        is False
    )


def test_missing_schema_version_table_fails_verification(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "history.sqlite3"
    )

    connection = sqlite3.connect(
        database_path
    )
    connection.close()

    metadata = _metadata(
        database_path
    )

    metadata_path = metadata.publish(
        tmp_path
    )

    assert (
        HistoryBackupMetadata.verify(
            metadata_path
        )
        is False
    )


def test_multiple_schema_version_rows_fail_verification(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "history.sqlite3"
    )
    _create_database(database_path)

    connection = sqlite3.connect(
        database_path
    )

    try:
        connection.execute(
            """
            INSERT INTO schema_version(version)
            VALUES (3)
            """
        )
        connection.commit()
    finally:
        connection.close()

    metadata = _metadata(
        database_path
    )

    metadata_path = metadata.publish(
        tmp_path
    )

    assert (
        HistoryBackupMetadata.verify(
            metadata_path
        )
        is False
    )


def test_publish_never_overwrites_metadata(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "history.sqlite3"
    )
    _create_database(database_path)

    metadata = _metadata(
        database_path
    )

    metadata_path = metadata.publish(
        tmp_path
    )

    original = metadata_path.read_bytes()

    with pytest.raises(
        FileExistsError,
    ):
        metadata.publish(
            tmp_path
        )

    assert (
        metadata_path.read_bytes()
        == original
    )


def test_database_file_must_be_basename() -> None:
    with pytest.raises(
        ValueError,
        match="must be a basename",
    ):
        HistoryBackupMetadata(
            database_file="../history.sqlite3",
            created_at=CREATED_AT,
            covered_through=COVERED_THROUGH,
            schema_version=3,
            sha256="a" * 64,
        )


def test_coverage_must_be_utc_midnight() -> None:
    with pytest.raises(
        ValueError,
        match="UTC day boundary",
    ):
        HistoryBackupMetadata(
            database_file="history.sqlite3",
            created_at=CREATED_AT,
            covered_through=datetime(
                2026,
                9,
                4,
                0,
                0,
                1,
                tzinfo=UTC,
            ),
            schema_version=3,
            sha256="a" * 64,
        )
