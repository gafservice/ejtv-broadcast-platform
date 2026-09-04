from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.noc.history.evidence_day_sealer import (
    EvidenceDaySealer,
)
from app.noc.history.filesystem_evidence_backup_repository import (
    EvidenceBackupError,
    FilesystemEvidenceBackupRepository,
)


DAY = date(2026, 9, 2)


def _source_directory(
    root: Path,
) -> Path:
    return (
        root
        / "2026"
        / "09"
        / "02"
    )


def _backup_directory(
    root: Path,
) -> Path:
    return (
        root
        / "2026"
        / "09"
        / "02"
    )


def _sealed_source(
    tmp_path,
) -> tuple[Path, FilesystemEvidenceBackupRepository]:
    source = tmp_path / "source"

    directory = _source_directory(
        source
    )

    directory.mkdir(
        parents=True
    )

    (
        directory
        / "events.jsonl"
    ).write_text(
        '{"event_id":"event-1"}\n',
        encoding="utf-8",
    )

    (
        directory
        / "alarm_transitions.jsonl"
    ).write_text(
        '{"transition_id":"transition-1"}\n',
        encoding="utf-8",
    )

    EvidenceDaySealer(
        source
    ).seal_day(
        DAY
    )

    return (
        source,
        FilesystemEvidenceBackupRepository(
            source
        ),
    )


def test_backup_day_copies_exact_primary_evidence(
    tmp_path,
) -> None:
    source, repository = _sealed_source(
        tmp_path
    )

    destination = tmp_path / "backups"

    result = repository.backup_day(
        day=DAY,
        destination=destination,
    )

    source_directory = _source_directory(
        source
    )

    backup_directory = _backup_directory(
        destination
    )

    assert result.path == backup_directory
    assert result.day == DAY

    assert sorted(
        path.name
        for path in backup_directory.iterdir()
    ) == [
        "alarm_transitions.jsonl",
        "events.jsonl",
        "manifest.sha256",
    ]

    for filename in (
        "alarm_transitions.jsonl",
        "events.jsonl",
        "manifest.sha256",
    ):
        assert (
            backup_directory
            / filename
        ).read_bytes() == (
            source_directory
            / filename
        ).read_bytes()


def test_backup_does_not_copy_evidence_lock(
    tmp_path,
) -> None:
    _, repository = _sealed_source(
        tmp_path
    )

    destination = tmp_path / "backups"

    repository.backup_day(
        day=DAY,
        destination=destination,
    )

    assert not (
        _backup_directory(destination)
        / ".evidence.lock"
    ).exists()


def test_open_day_is_not_backed_up(
    tmp_path,
) -> None:
    source = tmp_path / "source"

    directory = _source_directory(
        source
    )

    directory.mkdir(
        parents=True
    )

    (
        directory
        / "events.jsonl"
    ).write_text(
        '{"event_id":"event-1"}\n',
        encoding="utf-8",
    )

    repository = FilesystemEvidenceBackupRepository(
        source
    )

    destination = tmp_path / "backups"

    with pytest.raises(
        EvidenceBackupError,
        match="not sealed",
    ):
        repository.backup_day(
            day=DAY,
            destination=destination,
        )

    assert not _backup_directory(
        destination
    ).exists()


def test_tampered_sealed_day_is_not_backed_up(
    tmp_path,
) -> None:
    source, repository = _sealed_source(
        tmp_path
    )

    with (
        _source_directory(source)
        / "events.jsonl"
    ).open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            '{"tampered":true}\n'
        )

    destination = tmp_path / "backups"

    with pytest.raises(
        EvidenceBackupError,
        match="does not match manifest",
    ):
        repository.backup_day(
            day=DAY,
            destination=destination,
        )

    assert not _backup_directory(
        destination
    ).exists()


def test_published_backup_verifies(
    tmp_path,
) -> None:
    _, repository = _sealed_source(
        tmp_path
    )

    destination = tmp_path / "backups"

    repository.backup_day(
        day=DAY,
        destination=destination,
    )

    assert repository.verify_backup(
        day=DAY,
        destination=destination,
    ) is True


def test_verify_backup_detects_tampering(
    tmp_path,
) -> None:
    _, repository = _sealed_source(
        tmp_path
    )

    destination = tmp_path / "backups"

    repository.backup_day(
        day=DAY,
        destination=destination,
    )

    with (
        _backup_directory(destination)
        / "events.jsonl"
    ).open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            '{"tampered":true}\n'
        )

    assert repository.verify_backup(
        day=DAY,
        destination=destination,
    ) is False


def test_existing_backup_is_never_overwritten(
    tmp_path,
) -> None:
    _, repository = _sealed_source(
        tmp_path
    )

    destination = tmp_path / "backups"

    existing = _backup_directory(
        destination
    )

    existing.mkdir(
        parents=True
    )

    marker = existing / "existing.txt"

    marker.write_bytes(
        b"existing-backup"
    )

    with pytest.raises(
        FileExistsError,
        match="already exists",
    ):
        repository.backup_day(
            day=DAY,
            destination=destination,
        )

    assert marker.read_bytes() == b"existing-backup"


def test_invalid_destination_type_publishes_nothing(
    tmp_path,
) -> None:
    _, repository = _sealed_source(
        tmp_path
    )

    with pytest.raises(
        TypeError,
        match="destination must be a Path",
    ):
        repository.backup_day(
            day=DAY,
            destination="backups",
        )


def test_publish_race_never_overwrites_existing_backup(
    tmp_path,
    monkeypatch,
) -> None:
    _, repository = _sealed_source(
        tmp_path
    )

    destination = tmp_path / "backups"

    final_directory = _backup_directory(
        destination
    )

    original_publish = (
        repository._publish_without_overwrite
    )

    def concurrent_publish(
        *,
        temporary: Path,
        destination: Path,
    ) -> None:
        destination.mkdir(
            parents=True
        )

        marker = (
            destination
            / "winner.txt"
        )

        marker.write_bytes(
            b"winner-created-concurrently"
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
        repository.backup_day(
            day=DAY,
            destination=destination,
        )

    assert final_directory.is_dir()

    assert (
        final_directory
        / "winner.txt"
    ).read_bytes() == (
        b"winner-created-concurrently"
    )

    assert not (
        final_directory
        / "events.jsonl"
    ).exists()

    assert list(
        final_directory.parent.glob(
            ".02.*.tmp"
        )
    ) == []


def test_publish_race_with_empty_destination_never_replaces_winner(
    tmp_path,
    monkeypatch,
) -> None:
    _, repository = _sealed_source(
        tmp_path
    )

    destination = tmp_path / "backups"

    final_directory = _backup_directory(
        destination
    )

    original_publish = (
        repository._publish_without_overwrite
    )

    def concurrent_publish(
        *,
        temporary: Path,
        destination: Path,
    ) -> None:
        destination.mkdir(
            parents=True
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
        repository.backup_day(
            day=DAY,
            destination=destination,
        )

    assert final_directory.is_dir()

    assert list(
        final_directory.iterdir()
    ) == []

    assert list(
        final_directory.parent.glob(
            ".02.*.tmp"
        )
    ) == []


def test_directory_fsync_failure_keeps_published_backup(
    tmp_path,
    monkeypatch,
) -> None:
    _, repository = _sealed_source(
        tmp_path
    )

    destination = tmp_path / "backups"

    final_directory = _backup_directory(
        destination
    )

    original_fsync = (
        repository._fsync_directory
    )

    def fail_parent_fsync(
        path: Path,
    ) -> None:
        if path == final_directory.parent:
            raise RuntimeError(
                "forced parent fsync failure"
            )

        original_fsync(
            path
        )

    monkeypatch.setattr(
        repository,
        "_fsync_directory",
        fail_parent_fsync,
    )

    with pytest.raises(
        RuntimeError,
        match="forced parent fsync failure",
    ):
        repository.backup_day(
            day=DAY,
            destination=destination,
        )

    assert final_directory.is_dir()

    assert sorted(
        path.name
        for path in final_directory.iterdir()
    ) == [
        "alarm_transitions.jsonl",
        "events.jsonl",
        "manifest.sha256",
    ]

    assert repository.verify_backup(
        day=DAY,
        destination=destination,
    ) is True
