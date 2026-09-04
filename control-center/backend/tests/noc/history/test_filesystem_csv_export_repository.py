"""Tests for filesystem publication of derived CSV history."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.noc.history.filesystem_csv_export_repository import (
    FilesystemCsvExportRepository,
)


EVENTS_CSV = (
    "schema_version,record_type,event_id\n"
    "1,event,event-001\n"
)

ALARMS_CSV = (
    "schema_version,record_type,transition_id\n"
    "1,alarm_transition,transition-001\n"
)


def test_publish_creates_exact_csv_export(
    tmp_path,
) -> None:
    repository = (
        FilesystemCsvExportRepository()
    )

    destination = (
        tmp_path
        / "export-001"
    )

    result = repository.publish(
        destination=destination,
        events_csv=EVENTS_CSV,
        alarm_transitions_csv=ALARMS_CSV,
    )

    assert result.path == destination
    assert result.events_file == (
        destination
        / "events.csv"
    )
    assert result.alarm_transitions_file == (
        destination
        / "alarm_transitions.csv"
    )

    assert sorted(
        path.name
        for path in destination.iterdir()
    ) == [
        "alarm_transitions.csv",
        "events.csv",
    ]

    assert (
        destination
        / "events.csv"
    ).read_text(
        encoding="utf-8"
    ) == EVENTS_CSV

    assert (
        destination
        / "alarm_transitions.csv"
    ).read_text(
        encoding="utf-8"
    ) == ALARMS_CSV


def test_publish_preserves_utf8_and_newlines(
    tmp_path,
) -> None:
    repository = (
        FilesystemCsvExportRepository()
    )

    destination = (
        tmp_path
        / "export-utf8"
    )

    events_csv = (
        'title,description\n'
        '"Sesión número 1","Línea uno\nLínea dos"\n'
    )

    repository.publish(
        destination=destination,
        events_csv=events_csv,
        alarm_transitions_csv=ALARMS_CSV,
    )

    assert (
        destination
        / "events.csv"
    ).read_text(
        encoding="utf-8"
    ) == events_csv


def test_existing_export_is_never_overwritten(
    tmp_path,
) -> None:
    repository = (
        FilesystemCsvExportRepository()
    )

    destination = (
        tmp_path
        / "existing"
    )

    destination.mkdir()

    marker = (
        destination
        / "existing.txt"
    )
    marker.write_text(
        "preserve",
        encoding="utf-8",
    )

    with pytest.raises(
        FileExistsError,
        match="already exists",
    ):
        repository.publish(
            destination=destination,
            events_csv=EVENTS_CSV,
            alarm_transitions_csv=ALARMS_CSV,
        )

    assert marker.read_text(
        encoding="utf-8"
    ) == "preserve"


def test_invalid_destination_type_publishes_nothing(
    tmp_path,
) -> None:
    repository = (
        FilesystemCsvExportRepository()
    )

    with pytest.raises(
        TypeError,
        match="destination must be a Path",
    ):
        repository.publish(
            destination=str(
                tmp_path
                / "invalid"
            ),
            events_csv=EVENTS_CSV,
            alarm_transitions_csv=ALARMS_CSV,
        )


@pytest.mark.parametrize(
    (
        "events_csv",
        "alarm_transitions_csv",
        "message",
    ),
    (
        (
            b"events",
            ALARMS_CSV,
            "events_csv must be a str",
        ),
        (
            EVENTS_CSV,
            b"alarms",
            "alarm_transitions_csv must be a str",
        ),
    ),
)
def test_invalid_csv_content_type_is_rejected(
    tmp_path,
    events_csv,
    alarm_transitions_csv,
    message,
) -> None:
    repository = (
        FilesystemCsvExportRepository()
    )

    destination = (
        tmp_path
        / "invalid-content"
    )

    with pytest.raises(
        TypeError,
        match=message,
    ):
        repository.publish(
            destination=destination,
            events_csv=events_csv,
            alarm_transitions_csv=alarm_transitions_csv,
        )

    assert not destination.exists()


def test_publication_failure_removes_temporary_directory(
    tmp_path,
    monkeypatch,
) -> None:
    repository = (
        FilesystemCsvExportRepository()
    )

    destination = (
        tmp_path
        / "failed-export"
    )

    def fail_publish(
        *,
        temporary,
        destination,
    ):
        raise OSError(
            "simulated publication failure"
        )

    monkeypatch.setattr(
        repository,
        "_publish_without_overwrite",
        fail_publish,
    )

    with pytest.raises(
        OSError,
        match="simulated publication failure",
    ):
        repository.publish(
            destination=destination,
            events_csv=EVENTS_CSV,
            alarm_transitions_csv=ALARMS_CSV,
        )

    assert not destination.exists()

    assert not any(
        path.name.startswith(
            ".failed-export."
        )
        for path in tmp_path.iterdir()
    )


def test_parent_directory_is_created(
    tmp_path,
) -> None:
    repository = (
        FilesystemCsvExportRepository()
    )

    destination = (
        tmp_path
        / "nested"
        / "exports"
        / "export-001"
    )

    repository.publish(
        destination=destination,
        events_csv=EVENTS_CSV,
        alarm_transitions_csv=ALARMS_CSV,
    )

    assert destination.is_dir()


def test_concurrent_winner_is_never_replaced(
    tmp_path,
    monkeypatch,
) -> None:
    repository = (
        FilesystemCsvExportRepository()
    )

    destination = (
        tmp_path
        / "race-export"
    )

    original_publish = (
        repository._publish_without_overwrite
    )

    def publish_after_concurrent_winner(
        *,
        temporary,
        destination,
    ):
        destination.mkdir()

        marker = (
            destination
            / "winner.txt"
        )
        marker.write_text(
            "concurrent-winner",
            encoding="utf-8",
        )

        return original_publish(
            temporary=temporary,
            destination=destination,
        )

    monkeypatch.setattr(
        repository,
        "_publish_without_overwrite",
        publish_after_concurrent_winner,
    )

    with pytest.raises(
        FileExistsError,
        match="already exists",
    ):
        repository.publish(
            destination=destination,
            events_csv=EVENTS_CSV,
            alarm_transitions_csv=ALARMS_CSV,
        )

    assert (
        destination
        / "winner.txt"
    ).read_text(
        encoding="utf-8"
    ) == "concurrent-winner"

    assert not (
        destination
        / "events.csv"
    ).exists()

    assert not (
        destination
        / "alarm_transitions.csv"
    ).exists()

    assert not any(
        path.name.startswith(
            ".race-export."
        )
        for path in tmp_path.iterdir()
    )


def test_concurrent_winner_is_never_replaced(
    tmp_path,
    monkeypatch,
) -> None:
    repository = (
        FilesystemCsvExportRepository()
    )

    destination = (
        tmp_path
        / "race-export"
    )

    original_publish = (
        repository._publish_without_overwrite
    )

    def publish_after_concurrent_winner(
        *,
        temporary,
        destination,
    ):
        destination.mkdir()

        marker = (
            destination
            / "winner.txt"
        )
        marker.write_text(
            "concurrent-winner",
            encoding="utf-8",
        )

        return original_publish(
            temporary=temporary,
            destination=destination,
        )

    monkeypatch.setattr(
        repository,
        "_publish_without_overwrite",
        publish_after_concurrent_winner,
    )

    with pytest.raises(
        FileExistsError,
        match="already exists",
    ):
        repository.publish(
            destination=destination,
            events_csv=EVENTS_CSV,
            alarm_transitions_csv=ALARMS_CSV,
        )

    assert (
        destination
        / "winner.txt"
    ).read_text(
        encoding="utf-8"
    ) == "concurrent-winner"

    assert not (
        destination
        / "events.csv"
    ).exists()

    assert not (
        destination
        / "alarm_transitions.csv"
    ).exists()

    assert not any(
        path.name.startswith(
            ".race-export."
        )
        for path in tmp_path.iterdir()
    )
