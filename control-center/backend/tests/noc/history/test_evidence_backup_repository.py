from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.noc.history.evidence_backup_repository import (
    EvidenceBackupRepository,
    EvidenceBackupResult,
)


DAY = date(2026, 9, 2)


class _EvidenceBackupRepository:
    def backup_day(
        self,
        *,
        day: date,
        destination: Path,
    ) -> EvidenceBackupResult:
        return EvidenceBackupResult(
            path=destination,
            day=day,
        )


def test_runtime_protocol_accepts_compatible_repository() -> None:
    assert isinstance(
        _EvidenceBackupRepository(),
        EvidenceBackupRepository,
    )


def test_backup_result_accepts_valid_identity(
    tmp_path,
) -> None:
    path = tmp_path / "2026-09-02"

    result = EvidenceBackupResult(
        path=path,
        day=DAY,
    )

    assert result.path == path
    assert result.day == DAY


def test_backup_result_rejects_non_path() -> None:
    with pytest.raises(
        TypeError,
        match="path must be a Path",
    ):
        EvidenceBackupResult(
            path="2026-09-02",
            day=DAY,
        )


def test_backup_result_rejects_non_date(
    tmp_path,
) -> None:
    with pytest.raises(
        TypeError,
        match="day must be a date",
    ):
        EvidenceBackupResult(
            path=tmp_path / "2026-09-02",
            day="2026-09-02",
        )


def test_protocol_method_shape_can_be_called(
    tmp_path,
) -> None:
    repository = _EvidenceBackupRepository()

    destination = tmp_path / "2026-09-02"

    result = repository.backup_day(
        day=DAY,
        destination=destination,
    )

    assert result == EvidenceBackupResult(
        path=destination,
        day=DAY,
    )
