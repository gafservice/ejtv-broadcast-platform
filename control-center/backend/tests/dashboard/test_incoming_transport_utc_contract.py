"""UTC presentation contract for incoming transport evidence."""

from datetime import datetime, timedelta, timezone

from app.dashboard.renderers.incoming_transport_cards_renderer import (
    IncomingTransportCardsRenderer,
)


def test_equivalent_instants_render_as_same_utc_timestamp():
    renderer = IncomingTransportCardsRenderer()

    utc_value = datetime(
        2026, 10, 19, 16, 0,
        tzinfo=timezone.utc,
    )

    costa_rica_value = datetime(
        2026, 10, 19, 10, 0,
        tzinfo=timezone(timedelta(hours=-6)),
    )

    assert utc_value == costa_rica_value

    expected = "2026-10-19 16:00:00 UTC"

    assert renderer._format_observed_at(utc_value) == expected
    assert renderer._format_observed_at(costa_rica_value) == expected


def test_missing_timestamp_is_unavailable():
    renderer = IncomingTransportCardsRenderer()

    assert renderer._format_observed_at(None) == "N/A"


def test_naive_timestamp_is_not_labeled_utc():
    renderer = IncomingTransportCardsRenderer()

    naive_value = datetime(2026, 10, 19, 10, 0)

    assert renderer._format_observed_at(naive_value) == "N/A"
