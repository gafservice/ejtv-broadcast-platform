"""RED contract for incoming transport path availability duration."""

from datetime import datetime, timedelta, timezone

from app.dashboard.renderers.incoming_transport_cards_renderer import (
    IncomingTransportCardsRenderer,
)


REFERENCE = datetime(
    2026, 10, 29, 22, 0, tzinfo=timezone.utc
)


def test_availability_duration_is_formatted():
    since = REFERENCE - timedelta(
        hours=2,
        minutes=15,
        seconds=30,
    )

    result = (
        IncomingTransportCardsRenderer
        ._format_path_availability_duration(
            available=True,
            available_since=since,
            reference_at=REFERENCE,
        )
    )

    assert result == "2h 15m 30s"


def test_unavailable_path_has_no_active_duration():
    result = (
        IncomingTransportCardsRenderer
        ._format_path_availability_duration(
            available=False,
            available_since=REFERENCE,
            reference_at=REFERENCE,
        )
    )

    assert result == "N/A"


def test_missing_timestamp_is_unavailable():
    result = (
        IncomingTransportCardsRenderer
        ._format_path_availability_duration(
            available=True,
            available_since=None,
            reference_at=REFERENCE,
        )
    )

    assert result == "N/A"


def test_future_timestamp_is_rejected():
    result = (
        IncomingTransportCardsRenderer
        ._format_path_availability_duration(
            available=True,
            available_since=REFERENCE + timedelta(seconds=1),
            reference_at=REFERENCE,
        )
    )

    assert result == "N/A"


def test_naive_timestamp_is_rejected():
    result = (
        IncomingTransportCardsRenderer
        ._format_path_availability_duration(
            available=True,
            available_since=datetime(2026, 10, 29, 21, 0),
            reference_at=REFERENCE,
        )
    )

    assert result == "N/A"
