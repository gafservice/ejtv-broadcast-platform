"""Contract for resetting INCOMING bitrate history on source changes."""

from datetime import UTC, datetime, timedelta

from app.dashboard.services.incoming_transport_bitrate_window import (
    IncomingTransportBitrateWindow,
)


T0 = datetime(2026, 10, 19, 17, 0, tzinfo=UTC)


def test_reset_clears_only_selected_path_history():
    window = IncomingTransportBitrateWindow(window_seconds=60)

    window.observe(
        "ejtv",
        observed_at=T0,
        bitrate_mbps=4.0,
    )
    window.observe(
        "enlace",
        observed_at=T0,
        bitrate_mbps=7.0,
    )

    window.reset("ejtv")

    ejtv = window.get(
        "ejtv",
        observed_at=T0 + timedelta(seconds=1),
    )
    enlace = window.get(
        "enlace",
        observed_at=T0 + timedelta(seconds=1),
    )

    assert ejtv.average_mbps is None
    assert ejtv.minimum_mbps is None
    assert ejtv.maximum_mbps is None

    assert enlace.average_mbps == 7.0
    assert enlace.minimum_mbps == 7.0
    assert enlace.maximum_mbps == 7.0


def test_reset_allows_new_source_to_start_clean_history():
    window = IncomingTransportBitrateWindow(window_seconds=60)

    window.observe(
        "impact",
        observed_at=T0,
        bitrate_mbps=3.0,
    )

    window.reset("impact")

    window.observe(
        "impact",
        observed_at=T0 + timedelta(seconds=2),
        bitrate_mbps=6.0,
    )

    statistics = window.get(
        "impact",
        observed_at=T0 + timedelta(seconds=2),
    )

    assert statistics.average_mbps == 6.0
    assert statistics.minimum_mbps == 6.0
    assert statistics.maximum_mbps == 6.0


def test_reset_does_not_affect_other_paths():
    window = IncomingTransportBitrateWindow(window_seconds=60)

    for path, bitrate in (
        ("ejtv", 4.0),
        ("enlace", 5.0),
        ("impact", 6.0),
    ):
        window.observe(
            path,
            observed_at=T0,
            bitrate_mbps=bitrate,
        )

    window.reset("enlace")

    assert window.get(
        "ejtv",
        observed_at=T0,
    ).average_mbps == 4.0

    assert window.get(
        "impact",
        observed_at=T0,
    ).average_mbps == 6.0

    assert window.get(
        "enlace",
        observed_at=T0,
    ).average_mbps is None
