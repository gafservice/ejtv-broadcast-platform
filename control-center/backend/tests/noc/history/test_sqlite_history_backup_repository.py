from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.noc.history.history_backup_repository import (
    HistoryBackupRepository,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)
from app.noc.history.sqlite_history_backup_repository import (
    SQLiteHistoryBackupRepository,
)


UTC = timezone.utc

CREATED_AT = datetime(
    2026,
    9,
    4,
    9,
    0,
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


def _repository(
    tmp_path,
) -> tuple[
    SQLiteHistoryDatabase,
    SQLiteHistoryBackupRepository,
]:
    database = SQLiteHistoryDatabase(
        tmp_path / "live" / "history.sqlite3"
    )

    database.initialize()

    return (
        database,
        SQLiteHistoryBackupRepository(
            database
        ),
    )


def _insert_marker(
    connection: sqlite3.Connection,
    value: str,
) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS backup_test_marker (
            value TEXT PRIMARY KEY
        )
        """
    )

    connection.execute(
        """
        INSERT INTO backup_test_marker(value)
        VALUES (?)
        """,
        (value,),
    )

    connection.commit()


def _read_markers(
    path: Path,
) -> list[str]:
    connection = sqlite3.connect(path)

    try:
        rows = connection.execute(
            """
            SELECT value
            FROM backup_test_marker
            ORDER BY value
            """
        ).fetchall()
    finally:
        connection.close()

    return [
        str(row[0])
        for row in rows
    ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file_handle:
        for chunk in iter(
            lambda: file_handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def test_repository_satisfies_backup_protocol(
    tmp_path,
) -> None:
    _, repository = _repository(tmp_path)

    assert isinstance(
        repository,
        HistoryBackupRepository,
    )


def test_backup_creates_standalone_consistent_database(
    tmp_path,
) -> None:
    database, repository = _repository(tmp_path)

    with database.connect() as connection:
        _insert_marker(
            connection,
            "alpha",
        )

    destination = (
        tmp_path
        / "backups"
        / "history.sqlite3"
    )

    result = repository.create_backup(
        destination=destination,
        created_at=CREATED_AT,
        covered_through=COVERED_THROUGH,
    )

    assert result.path == destination
    assert result.created_at == CREATED_AT
    assert destination.is_file()

    assert _read_markers(
        destination
    ) == ["alpha"]

    check_connection = sqlite3.connect(
        destination
    )

    try:
        integrity = check_connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()
    finally:
        check_connection.close()

    assert integrity == ("ok",)


def test_backup_sha256_matches_published_file(
    tmp_path,
) -> None:
    database, repository = _repository(tmp_path)

    with database.connect() as connection:
        _insert_marker(
            connection,
            "sha-test",
        )

    destination = (
        tmp_path / "backup.sqlite3"
    )

    result = repository.create_backup(
        destination=destination,
        created_at=CREATED_AT,
        covered_through=COVERED_THROUGH,
    )

    assert result.sha256 == _sha256(
        destination
    )


def test_backup_includes_committed_data_while_source_wal_is_active(
    tmp_path,
) -> None:
    database, repository = _repository(tmp_path)

    writer = database.connect()

    try:
        _insert_marker(
            writer,
            "committed-in-wal",
        )

        journal_mode = writer.execute(
            "PRAGMA journal_mode"
        ).fetchone()

        assert journal_mode is not None
        assert str(
            journal_mode[0]
        ).lower() == "wal"

        wal_path = Path(
            f"{database.path}-wal"
        )

        assert wal_path.exists()
        assert wal_path.stat().st_size > 0

        destination = (
            tmp_path
            / "backups"
            / "wal-backup.sqlite3"
        )

        repository.create_backup(
            destination=destination,
            created_at=CREATED_AT,
            covered_through=COVERED_THROUGH,
        )

        assert _read_markers(
            destination
        ) == ["committed-in-wal"]
    finally:
        writer.close()


def test_uncommitted_source_transaction_is_not_copied(
    tmp_path,
) -> None:
    database, repository = _repository(tmp_path)

    with database.connect() as connection:
        _insert_marker(
            connection,
            "committed",
        )

    writer = database.connect()

    try:
        writer.execute(
            """
            INSERT INTO backup_test_marker(value)
            VALUES (?)
            """,
            ("not-committed",),
        )

        destination = (
            tmp_path / "backup.sqlite3"
        )

        repository.create_backup(
            destination=destination,
            created_at=CREATED_AT,
            covered_through=COVERED_THROUGH,
        )

        assert _read_markers(
            destination
        ) == ["committed"]
    finally:
        writer.rollback()
        writer.close()


def test_existing_destination_is_never_overwritten(
    tmp_path,
) -> None:
    _, repository = _repository(tmp_path)

    destination = (
        tmp_path / "backup.sqlite3"
    )

    original = b"existing-backup"

    destination.write_bytes(
        original
    )

    with pytest.raises(
        FileExistsError,
        match="already exists",
    ):
        repository.create_backup(
            destination=destination,
            created_at=CREATED_AT,
            covered_through=COVERED_THROUGH,
        )

    assert destination.read_bytes() == original


def test_failed_backup_does_not_publish_destination(
    tmp_path,
    monkeypatch,
) -> None:
    _, repository = _repository(tmp_path)

    destination = (
        tmp_path / "backup.sqlite3"
    )

    def fail_verification(
        path: Path,
    ) -> None:
        raise RuntimeError(
            "forced verification failure"
        )

    monkeypatch.setattr(
        repository,
        "_verify_integrity",
        fail_verification,
    )

    with pytest.raises(
        RuntimeError,
        match="forced verification failure",
    ):
        repository.create_backup(
            destination=destination,
            created_at=CREATED_AT,
            covered_through=COVERED_THROUGH,
        )

    assert not destination.exists()

    temporary_files = list(
        tmp_path.glob(
            ".backup.sqlite3.*.tmp"
        )
    )

    assert temporary_files == []


def test_destination_must_be_path(
    tmp_path,
) -> None:
    _, repository = _repository(tmp_path)

    with pytest.raises(
        TypeError,
        match="destination must be a Path",
    ):
        repository.create_backup(
            destination="backup.sqlite3",
            created_at=CREATED_AT,
            covered_through=COVERED_THROUGH,
        )


def test_created_at_must_be_timezone_aware(
    tmp_path,
) -> None:
    _, repository = _repository(tmp_path)

    with pytest.raises(
        ValueError,
        match="created_at must be timezone-aware",
    ):
        repository.create_backup(
            destination=tmp_path / "backup.sqlite3",
            created_at=datetime(
                2026,
                9,
                4,
                9,
            ),
            covered_through=COVERED_THROUGH,
        )


def test_created_at_must_be_utc(
    tmp_path,
) -> None:
    _, repository = _repository(tmp_path)

    with pytest.raises(
        ValueError,
        match="created_at must be expressed in UTC",
    ):
        repository.create_backup(
            destination=tmp_path / "backup.sqlite3",
            created_at=datetime(
                2026,
                9,
                4,
                3,
                tzinfo=timezone(
                    -timedelta(hours=6)
                ),
            ),
            covered_through=COVERED_THROUGH,
        )


def test_backup_preserves_current_schema_version(
    tmp_path,
) -> None:
    database, repository = _repository(tmp_path)

    destination = (
        tmp_path / "backup.sqlite3"
    )

    repository.create_backup(
        destination=destination,
        created_at=CREATED_AT,
        covered_through=COVERED_THROUGH,
    )

    source = database.connect()
    backup = sqlite3.connect(destination)

    try:
        source_version = source.execute(
            """
            SELECT version
            FROM schema_version
            LIMIT 1
            """
        ).fetchone()

        backup_version = backup.execute(
            """
            SELECT version
            FROM schema_version
            LIMIT 1
            """
        ).fetchone()
    finally:
        source.close()
        backup.close()

    assert source_version is not None
    assert backup_version is not None
    assert backup_version[0] == source_version[0]


def test_published_backup_needs_no_wal_or_shm(
    tmp_path,
) -> None:
    database, repository = _repository(tmp_path)

    writer = database.connect()

    try:
        _insert_marker(
            writer,
            "standalone",
        )

        destination = (
            tmp_path / "backup.sqlite3"
        )

        repository.create_backup(
            destination=destination,
            created_at=CREATED_AT,
            covered_through=COVERED_THROUGH,
        )

        assert destination.exists()

        assert not Path(
            f"{destination}-wal"
        ).exists()

        assert not Path(
            f"{destination}-shm"
        ).exists()

        connection = sqlite3.connect(
            f"file:{destination}?mode=ro",
            uri=True,
        )

        try:
            row = connection.execute(
                """
                SELECT value
                FROM backup_test_marker
                """
            ).fetchone()

            integrity = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()
        finally:
            connection.close()

        assert row == ("standalone",)
        assert integrity == ("ok",)
    finally:
        writer.close()


def test_publish_race_never_overwrites_existing_backup(
    tmp_path,
    monkeypatch,
) -> None:
    database, repository = _repository(tmp_path)

    with database.connect() as connection:
        _insert_marker(
            connection,
            "source",
        )

    destination = (
        tmp_path / "backup.sqlite3"
    )

    original = b"winner-created-concurrently"

    original_publish = (
        repository._publish_without_overwrite
    )

    def concurrent_publish(
        *,
        temporary: Path,
        destination: Path,
    ) -> None:
        destination.write_bytes(
            original
        )

        original_publish(
            temporary=temporary,
            destination=destination,
        )

    monkeypatch.setattr(
        repository,
        "_publish_without_overwrite",
        concurrent_publish,
    )

    with pytest.raises(
        FileExistsError,
        match="already exists",
    ):
        repository.create_backup(
            destination=destination,
            created_at=CREATED_AT,
            covered_through=COVERED_THROUGH,
        )

    assert destination.read_bytes() == original

    assert list(
        tmp_path.glob(
            ".backup.sqlite3.*.tmp"
        )
    ) == []


def test_sha256_failure_leaves_no_published_or_temporary_file(
    tmp_path,
    monkeypatch,
) -> None:
    _, repository = _repository(tmp_path)

    destination = (
        tmp_path / "backup.sqlite3"
    )

    def fail_sha256(
        path: Path,
    ) -> str:
        raise RuntimeError(
            "forced sha256 failure"
        )

    monkeypatch.setattr(
        repository,
        "_sha256",
        fail_sha256,
    )

    with pytest.raises(
        RuntimeError,
        match="forced sha256 failure",
    ):
        repository.create_backup(
            destination=destination,
            created_at=CREATED_AT,
            covered_through=COVERED_THROUGH,
        )

    assert not destination.exists()

    assert list(
        tmp_path.glob(
            ".backup.sqlite3.*.tmp"
        )
    ) == []


def test_directory_fsync_failure_keeps_published_backup(
    tmp_path,
    monkeypatch,
) -> None:
    database, repository = _repository(tmp_path)

    with database.connect() as connection:
        _insert_marker(
            connection,
            "published",
        )

    destination = (
        tmp_path / "backup.sqlite3"
    )

    def fail_directory_fsync(
        path: Path,
    ) -> None:
        raise RuntimeError(
            "forced directory fsync failure"
        )

    monkeypatch.setattr(
        repository,
        "_fsync_directory",
        fail_directory_fsync,
    )

    with pytest.raises(
        RuntimeError,
        match="forced directory fsync failure",
    ):
        repository.create_backup(
            destination=destination,
            created_at=CREATED_AT,
            covered_through=COVERED_THROUGH,
        )

    # Publication already happened. The cleanup path must never
    # remove the immutable published backup.
    assert destination.exists()

    assert _read_markers(
        destination
    ) == ["published"]


def test_backup_result_reports_requested_coverage(
    tmp_path,
) -> None:
    _, repository = _repository(tmp_path)

    destination = (
        tmp_path / "backup.sqlite3"
    )

    result = repository.create_backup(
        destination=destination,
        created_at=CREATED_AT,
        covered_through=COVERED_THROUGH,
    )

    assert (
        result.covered_through
        == COVERED_THROUGH
    )


def test_invalid_coverage_publishes_nothing(
    tmp_path,
) -> None:
    _, repository = _repository(tmp_path)

    destination = (
        tmp_path / "backup.sqlite3"
    )

    with pytest.raises(
        ValueError,
        match=(
            "covered_through must be aligned "
            "to a UTC day boundary"
        ),
    ):
        repository.create_backup(
            destination=destination,
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
        )

    assert not destination.exists()

    assert list(
        tmp_path.glob(
            ".backup.sqlite3.*.tmp"
        )
    ) == []
