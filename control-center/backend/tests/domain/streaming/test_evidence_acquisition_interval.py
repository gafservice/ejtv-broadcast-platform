"""Contract tests for evidence acquisition intervals."""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.streaming.evidence_acquisition_interval import (
    EvidenceAcquisitionInterval,
)


START = datetime(
    2026, 10, 20, 12, 0, 0, tzinfo=timezone.utc
)


def make_interval(
    *,
    started_at=START,
    completed_at=None,
    source="mediamtx.metrics",
):
    if completed_at is None:
        completed_at = started_at + timedelta(milliseconds=250)

    return EvidenceAcquisitionInterval(
        started_at=started_at,
        completed_at=completed_at,
        source=source,
    )


def test_valid_acquisition_interval():
    interval = make_interval()

    assert interval.started_at == START
    assert interval.completed_at == START + timedelta(milliseconds=250)
    assert interval.source == "mediamtx.metrics"
    assert interval.duration_seconds == pytest.approx(0.25)


def test_zero_duration_is_valid():
    interval = make_interval(completed_at=START)

    assert interval.duration_seconds == 0.0


def test_completed_before_started_is_rejected():
    with pytest.raises(ValueError):
        make_interval(
            completed_at=START - timedelta(microseconds=1)
        )


@pytest.mark.parametrize(
    "field",
    ["started_at", "completed_at"],
)
def test_naive_datetime_is_rejected(field):
    kwargs = {
        "started_at": START,
        "completed_at": START,
    }

    kwargs[field] = START.replace(tzinfo=None)

    with pytest.raises(ValueError):
        make_interval(**kwargs)


@pytest.mark.parametrize(
    "field",
    ["started_at", "completed_at"],
)
def test_non_utc_datetime_is_rejected(field):
    kwargs = {
        "started_at": START,
        "completed_at": START,
    }

    kwargs[field] = START.astimezone(
        timezone(timedelta(hours=-6))
    )

    with pytest.raises(ValueError):
        make_interval(**kwargs)


@pytest.mark.parametrize(
    "source",
    ["", " ", "\t", "\n"],
)
def test_blank_source_is_rejected(source):
    with pytest.raises(ValueError):
        make_interval(source=source)


def test_source_is_preserved_without_protocol_assumptions():
    interval = make_interval(source="packet.analyzer")

    assert interval.source == "packet.analyzer"


def test_interval_is_immutable():
    from dataclasses import FrozenInstanceError

    interval = make_interval()

    with pytest.raises(FrozenInstanceError):
        interval.source = "modified"


def test_duration_is_derived_from_timestamps():
    interval = make_interval(
        completed_at=START + timedelta(seconds=2, milliseconds=125)
    )

    assert interval.duration_seconds == pytest.approx(2.125)
