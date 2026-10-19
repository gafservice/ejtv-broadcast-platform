"""Contract tests for INCOMING transport bitrate rolling statistics."""

from datetime import UTC, datetime, timedelta

from app.dashboard.services.incoming_transport_bitrate_window import (
    IncomingTransportBitrateWindow,
)


T0 = datetime(2026, 10, 19, 17, 0, tzinfo=UTC)


def test_initial_statistics_are_unavailable():
    window = IncomingTransportBitrateWindow(window_seconds=60)

    result = window.get("ejtv", observed_at=T0)

    assert result.average_mbps is None
    assert result.minimum_mbps is None
    assert result.maximum_mbps is None


def test_valid_samples_produce_average_minimum_and_maximum():
    window = IncomingTransportBitrateWindow(window_seconds=60)

    window.observe("ejtv", observed_at=T0, bitrate_mbps=4.0)
    window.observe(
        "ejtv",
        observed_at=T0 + timedelta(seconds=5),
        bitrate_mbps=6.0,
    )
    window.observe(
        "ejtv",
        observed_at=T0 + timedelta(seconds=10),
        bitrate_mbps=5.0,
    )

    result = window.get(
        "ejtv",
        observed_at=T0 + timedelta(seconds=10),
    )

    assert result.average_mbps == 5.0
    assert result.minimum_mbps == 4.0
    assert result.maximum_mbps == 6.0


def test_paths_are_isolated():
    window = IncomingTransportBitrateWindow(window_seconds=60)

    window.observe("ejtv", observed_at=T0, bitrate_mbps=4.0)
    window.observe("enlace", observed_at=T0, bitrate_mbps=9.0)

    assert window.get("ejtv", observed_at=T0).average_mbps == 4.0
    assert window.get("enlace", observed_at=T0).average_mbps == 9.0
    assert window.get("impact", observed_at=T0).average_mbps is None


def test_zero_bitrate_is_valid():
    window = IncomingTransportBitrateWindow(window_seconds=60)

    window.observe("impact", observed_at=T0, bitrate_mbps=0.0)

    result = window.get("impact", observed_at=T0)

    assert result.average_mbps == 0.0
    assert result.minimum_mbps == 0.0
    assert result.maximum_mbps == 0.0


def test_unavailable_sample_is_not_added():
    window = IncomingTransportBitrateWindow(window_seconds=60)

    window.observe("ejtv", observed_at=T0, bitrate_mbps=4.0)
    window.observe(
        "ejtv",
        observed_at=T0 + timedelta(seconds=5),
        bitrate_mbps=None,
    )

    result = window.get(
        "ejtv",
        observed_at=T0 + timedelta(seconds=5),
    )

    assert result.average_mbps == 4.0
    assert result.minimum_mbps == 4.0
    assert result.maximum_mbps == 4.0


def test_samples_outside_window_expire():
    window = IncomingTransportBitrateWindow(window_seconds=60)

    window.observe("ejtv", observed_at=T0, bitrate_mbps=4.0)
    window.observe(
        "ejtv",
        observed_at=T0 + timedelta(seconds=30),
        bitrate_mbps=6.0,
    )

    result = window.get(
        "ejtv",
        observed_at=T0 + timedelta(seconds=65),
    )

    assert result.average_mbps == 6.0
    assert result.minimum_mbps == 6.0
    assert result.maximum_mbps == 6.0


def test_all_expired_returns_unavailable():
    window = IncomingTransportBitrateWindow(window_seconds=60)

    window.observe("ejtv", observed_at=T0, bitrate_mbps=4.0)

    result = window.get(
        "ejtv",
        observed_at=T0 + timedelta(seconds=61),
    )

    assert result.average_mbps is None
    assert result.minimum_mbps is None
    assert result.maximum_mbps is None


def test_negative_bitrate_is_rejected():
    window = IncomingTransportBitrateWindow(window_seconds=60)

    try:
        window.observe("ejtv", observed_at=T0, bitrate_mbps=-1.0)
    except ValueError:
        pass
    else:
        raise AssertionError("Negative bitrate must be rejected")


def test_non_positive_window_is_rejected():
    for seconds in (0, -5):
        try:
            IncomingTransportBitrateWindow(window_seconds=seconds)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid window must be rejected")
