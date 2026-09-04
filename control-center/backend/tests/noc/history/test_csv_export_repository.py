"""Tests for the CSV history export repository contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.noc.history.csv_export_repository import (
    CsvExportRepository,
    CsvExportResult,
)


def test_csv_export_result_accepts_paths() -> None:
    result = CsvExportResult(
        path=Path("/tmp/export"),
        events_file=Path(
            "/tmp/export/events.csv"
        ),
        alarm_transitions_file=Path(
            "/tmp/export/alarm_transitions.csv"
        ),
    )

    assert result.path == Path(
        "/tmp/export"
    )
    assert result.events_file == Path(
        "/tmp/export/events.csv"
    )
    assert result.alarm_transitions_file == Path(
        "/tmp/export/alarm_transitions.csv"
    )


@pytest.mark.parametrize(
    (
        "field",
        "value",
        "message",
    ),
    (
        (
            "path",
            "/tmp/export",
            "path must be a Path",
        ),
        (
            "events_file",
            "/tmp/export/events.csv",
            "events_file must be a Path",
        ),
        (
            "alarm_transitions_file",
            "/tmp/export/alarm_transitions.csv",
            (
                "alarm_transitions_file "
                "must be a Path"
            ),
        ),
    ),
)
def test_csv_export_result_rejects_invalid_paths(
    field,
    value,
    message,
) -> None:
    arguments = {
        "path": Path("/tmp/export"),
        "events_file": Path(
            "/tmp/export/events.csv"
        ),
        "alarm_transitions_file": Path(
            "/tmp/export/alarm_transitions.csv"
        ),
    }

    arguments[field] = value

    with pytest.raises(
        TypeError,
        match=message,
    ):
        CsvExportResult(**arguments)


def test_csv_export_repository_is_runtime_protocol() -> None:
    class Repository:
        def publish(
            self,
            *,
            destination,
            events_csv,
            alarm_transitions_csv,
        ):
            raise NotImplementedError

    assert isinstance(
        Repository(),
        CsvExportRepository,
    )
