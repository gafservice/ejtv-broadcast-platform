from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.noc.history.history_backup_repository import (
    HistoryBackupRepository,
    HistoryBackupResult,
)


UTC = timezone.utc

CREATED_AT = datetime(
    2026,
    9,
    4,
    8,
    30,
    tzinfo=UTC,
)

SHA256 = "a" * 64

COVERED_THROUGH = datetime(
    2026,
    9,
    4,
    0,
    0,
    tzinfo=UTC,
)


class _BackupRepository:
    def create_backup(
        self,
        *,
        destination: Path,
        created_at: datetime,
        covered_through: datetime,
    ) -> HistoryBackupResult:
        return HistoryBackupResult(
            path=destination,
            created_at=created_at,
            sha256=SHA256,
            covered_through=covered_through,
        )


def test_runtime_protocol_accepts_compatible_repository() -> None:
    assert isinstance(
        _BackupRepository(),
        HistoryBackupRepository,
    )


def test_backup_result_accepts_valid_metadata(
    tmp_path,
) -> None:
    path = tmp_path / "history-backup.sqlite3"

    result = HistoryBackupResult(
        path=path,
        created_at=CREATED_AT,
        covered_through=COVERED_THROUGH,
        sha256=SHA256,
    )

    assert result.path == path
    assert result.created_at == CREATED_AT
    assert result.sha256 == SHA256


def test_backup_result_rejects_non_path() -> None:
    with pytest.raises(
        TypeError,
        match="path must be a Path",
    ):
        HistoryBackupResult(
            path="backup.sqlite3",
            created_at=CREATED_AT,
            covered_through=COVERED_THROUGH,
            sha256=SHA256,
        )


def test_backup_result_rejects_naive_created_at(
    tmp_path,
) -> None:
    with pytest.raises(
        ValueError,
        match="created_at must be timezone-aware",
    ):
        HistoryBackupResult(
            path=tmp_path / "backup.sqlite3",
            created_at=datetime(
                2026,
                9,
                4,
                8,
                30,
            ),
            sha256=SHA256,
            covered_through=COVERED_THROUGH,
        )


def test_backup_result_rejects_non_utc_created_at(
    tmp_path,
) -> None:
    with pytest.raises(
        ValueError,
        match="created_at must be expressed in UTC",
    ):
        HistoryBackupResult(
            path=tmp_path / "backup.sqlite3",
            created_at=datetime(
                2026,
                9,
                4,
                2,
                30,
                tzinfo=timezone(
                    -timedelta(hours=6)
                ),
            ),
            sha256=SHA256,
            covered_through=COVERED_THROUGH,
        )


@pytest.mark.parametrize(
    "sha256",
    (
        "",
        "a" * 63,
        "a" * 65,
        "z" * 64,
    ),
)
def test_backup_result_rejects_invalid_sha256(
    tmp_path,
    sha256: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="sha256 must contain 64 hexadecimal characters",
    ):
        HistoryBackupResult(
            path=tmp_path / "backup.sqlite3",
            created_at=CREATED_AT,
            covered_through=COVERED_THROUGH,
            sha256=sha256,
        )


def test_backup_result_rejects_non_string_sha256(
    tmp_path,
) -> None:
    with pytest.raises(
        TypeError,
        match="sha256 must be a str",
    ):
        HistoryBackupResult(
            path=tmp_path / "backup.sqlite3",
            created_at=CREATED_AT,
            covered_through=COVERED_THROUGH,
            sha256=123,
        )


def test_protocol_method_shape_can_be_called(
    tmp_path,
) -> None:
    repository = _BackupRepository()

    destination = (
        tmp_path / "history-backup.sqlite3"
    )

    result = repository.create_backup(
        destination=destination,
        created_at=CREATED_AT,
        covered_through=COVERED_THROUGH,
    )

    assert result == HistoryBackupResult(
        path=destination,
        created_at=CREATED_AT,
        covered_through=COVERED_THROUGH,
        sha256=SHA256,
    )


def test_backup_result_exposes_coverage_boundary(
    tmp_path,
) -> None:
    result = HistoryBackupResult(
        path=tmp_path / "backup.sqlite3",
        created_at=CREATED_AT,
        sha256=SHA256,
        covered_through=COVERED_THROUGH,
    )

    assert (
        result.covered_through
        == COVERED_THROUGH
    )


def test_backup_result_rejects_naive_covered_through(
    tmp_path,
) -> None:
    with pytest.raises(
        ValueError,
        match="covered_through must be timezone-aware",
    ):
        HistoryBackupResult(
            path=tmp_path / "backup.sqlite3",
            created_at=CREATED_AT,
            sha256=SHA256,
            covered_through=datetime(
                2026,
                9,
                4,
            ),
        )


def test_backup_result_rejects_non_utc_covered_through(
    tmp_path,
) -> None:
    with pytest.raises(
        ValueError,
        match="covered_through must be expressed in UTC",
    ):
        HistoryBackupResult(
            path=tmp_path / "backup.sqlite3",
            created_at=CREATED_AT,
            sha256=SHA256,
            covered_through=datetime(
                2026,
                9,
                3,
                18,
                tzinfo=timezone(
                    -timedelta(hours=6)
                ),
            ),
        )


def test_backup_result_rejects_non_midnight_coverage(
    tmp_path,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "covered_through must be aligned "
            "to a UTC day boundary"
        ),
    ):
        HistoryBackupResult(
            path=tmp_path / "backup.sqlite3",
            created_at=CREATED_AT,
            sha256=SHA256,
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


def test_backup_result_rejects_coverage_after_creation(
    tmp_path,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "covered_through must not be later "
            "than created_at"
        ),
    ):
        HistoryBackupResult(
            path=tmp_path / "backup.sqlite3",
            created_at=CREATED_AT,
            sha256=SHA256,
            covered_through=datetime(
                2026,
                9,
                5,
                tzinfo=UTC,
            ),
        )
