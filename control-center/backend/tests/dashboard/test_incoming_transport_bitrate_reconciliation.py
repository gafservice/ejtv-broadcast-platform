"""Contracts for dynamic INCOMING bitrate path reconciliation."""

from datetime import UTC, datetime, timedelta

from app.dashboard.services.incoming_transport_bitrate_window import (
    IncomingTransportBitrateWindow,
)


T0 = datetime(2026, 10, 19, 18, 0, tzinfo=UTC)


def _observe(
    window: IncomingTransportBitrateWindow,
    path: str,
    bitrate: float,
) -> None:
    window.observe(
        path,
        observed_at=T0,
        bitrate_mbps=bitrate,
    )


def test_reconcile_preserves_all_known_paths():
    window = IncomingTransportBitrateWindow()

    expected = {
        "ejtv": 4.0,
        "enlace": 5.0,
        "impact": 6.0,
        "canal-04": 7.0,
        "canal-05": 8.0,
    }

    for path, bitrate in expected.items():
        _observe(window, path, bitrate)

    window.reconcile_paths(tuple(expected))

    for path, bitrate in expected.items():
        statistics = window.get(
            path,
            observed_at=T0,
        )
        assert statistics.average_mbps == bitrate


def test_reconcile_removes_retired_path_history():
    window = IncomingTransportBitrateWindow()

    _observe(window, "ejtv", 4.0)
    _observe(window, "enlace", 5.0)
    _observe(window, "canal-retirado", 9.0)

    window.reconcile_paths(("ejtv", "enlace"))

    assert window.get(
        "canal-retirado",
        observed_at=T0,
    ).average_mbps is None

    assert "canal-retirado" not in window._samples
    assert "canal-retirado" not in window._last_observed_at


def test_reconcile_empty_inventory_clears_all_history():
    window = IncomingTransportBitrateWindow()

    _observe(window, "ejtv", 4.0)
    _observe(window, "enlace", 5.0)

    window.reconcile_paths(())

    assert window._samples == {}
    assert window._last_observed_at == {}


def test_reconcile_supports_new_paths_after_removal():
    window = IncomingTransportBitrateWindow()

    _observe(window, "ejtv", 4.0)
    _observe(window, "canal-antiguo", 3.0)

    window.reconcile_paths(("ejtv", "canal-nuevo"))

    window.observe(
        "canal-nuevo",
        observed_at=T0 + timedelta(seconds=1),
        bitrate_mbps=7.5,
    )

    assert window.get(
        "canal-nuevo",
        observed_at=T0 + timedelta(seconds=1),
    ).average_mbps == 7.5

    assert window.get(
        "canal-antiguo",
        observed_at=T0 + timedelta(seconds=1),
    ).average_mbps is None


def test_reconcile_is_independent_of_channel_count():
    window = IncomingTransportBitrateWindow()

    paths = tuple(
        f"canal-{index:03d}"
        for index in range(1, 101)
    )

    for index, path in enumerate(paths, start=1):
        _observe(window, path, float(index))

    window.reconcile_paths(paths)

    assert len(window._samples) == 100
    assert len(window._last_observed_at) == 100

    assert window.get(
        "canal-001",
        observed_at=T0,
    ).average_mbps == 1.0

    assert window.get(
        "canal-100",
        observed_at=T0,
    ).average_mbps == 100.0
