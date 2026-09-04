"""Tests for the NOC historical CSV export HTTP contract."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.api.schemas.noc_history import HistoryCsvExportRequest


def test_history_csv_export_request_accepts_utc_interval() -> None:
    request = HistoryCsvExportRequest(
        start="2026-09-01T00:00:00Z",
        end="2026-09-02T00:00:00Z",
    )

    assert request.start == datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )
    assert request.end == datetime(
        2026,
        9,
        2,
        tzinfo=timezone.utc,
    )


@pytest.mark.parametrize(
    ("field_name", "start", "end"),
    [
        (
            "start",
            "2026-09-01T00:00:00",
            "2026-09-02T00:00:00Z",
        ),
        (
            "end",
            "2026-09-01T00:00:00Z",
            "2026-09-02T00:00:00",
        ),
    ],
)
def test_history_csv_export_request_rejects_naive_timestamp(
    field_name: str,
    start: str,
    end: str,
) -> None:
    with pytest.raises(
        ValidationError,
        match=(
            rf"{field_name} must be timezone-aware and UTC"
        ),
    ):
        HistoryCsvExportRequest(
            start=start,
            end=end,
        )


@pytest.mark.parametrize(
    ("field_name", "start", "end"),
    [
        (
            "start",
            "2026-08-31T18:00:00-06:00",
            "2026-09-02T00:00:00Z",
        ),
        (
            "end",
            "2026-09-01T00:00:00Z",
            "2026-09-01T18:00:00-06:00",
        ),
    ],
)
def test_history_csv_export_request_rejects_non_utc_offset(
    field_name: str,
    start: str,
    end: str,
) -> None:
    with pytest.raises(
        ValidationError,
        match=(
            rf"{field_name} must be timezone-aware and UTC"
        ),
    ):
        HistoryCsvExportRequest(
            start=start,
            end=end,
        )


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (
            "2026-09-01T00:00:00Z",
            "2026-09-01T00:00:00Z",
        ),
        (
            "2026-09-02T00:00:00Z",
            "2026-09-01T00:00:00Z",
        ),
    ],
)
def test_history_csv_export_request_rejects_empty_or_reverse_interval(
    start: str,
    end: str,
) -> None:
    with pytest.raises(
        ValidationError,
        match="start must be earlier than end",
    ):
        HistoryCsvExportRequest(
            start=start,
            end=end,
        )


def test_history_csv_export_request_requires_start() -> None:
    with pytest.raises(ValidationError):
        HistoryCsvExportRequest.model_validate(
            {
                "end": "2026-09-02T00:00:00Z",
            }
        )


def test_history_csv_export_request_requires_end() -> None:
    with pytest.raises(ValidationError):
        HistoryCsvExportRequest.model_validate(
            {
                "start": "2026-09-01T00:00:00Z",
            }
        )


def test_history_csv_export_request_rejects_invalid_datetime() -> None:
    with pytest.raises(ValidationError):
        HistoryCsvExportRequest.model_validate(
            {
                "start": "not-a-datetime",
                "end": "2026-09-02T00:00:00Z",
            }
        )


def test_history_csv_export_request_rejects_unknown_fields() -> None:
    with pytest.raises(
        ValidationError,
        match="Extra inputs are not permitted",
    ):
        HistoryCsvExportRequest.model_validate(
            {
                "start": "2026-09-01T00:00:00Z",
                "end": "2026-09-02T00:00:00Z",
                "destination": "../../outside",
            }
        )
