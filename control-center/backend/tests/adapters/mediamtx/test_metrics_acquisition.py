"""Contract RED for immutable shared MediaMTX metrics acquisition."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from app.adapters.mediamtx.metrics_parser import (
    MediaMTXMetricsParser,
)
from app.domain.streaming.evidence_acquisition_interval import (
    EvidenceAcquisitionInterval,
)


OBSERVED_AT = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def make_snapshot():
    return MediaMTXMetricsParser().parse(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="read"} 12.5'
    )


def make_interval():
    return EvidenceAcquisitionInterval(
        started_at=OBSERVED_AT,
        completed_at=OBSERVED_AT + timedelta(milliseconds=50),
        source="mediamtx.metrics",
    )


def test_preserves_snapshot_identity():
    from app.adapters.mediamtx.metrics_acquisition import (
        MediaMTXMetricsAcquisition,
    )

    snapshot = make_snapshot()

    acquisition = MediaMTXMetricsAcquisition(
        snapshot=snapshot,
        interval=make_interval(),
    )

    assert acquisition.snapshot is snapshot


def test_preserves_interval_identity():
    from app.adapters.mediamtx.metrics_acquisition import (
        MediaMTXMetricsAcquisition,
    )

    interval = make_interval()

    acquisition = MediaMTXMetricsAcquisition(
        snapshot=make_snapshot(),
        interval=interval,
    )

    assert acquisition.interval is interval


def test_is_immutable():
    from app.adapters.mediamtx.metrics_acquisition import (
        MediaMTXMetricsAcquisition,
    )

    acquisition = MediaMTXMetricsAcquisition(
        snapshot=make_snapshot(),
        interval=make_interval(),
    )

    with pytest.raises(FrozenInstanceError):
        acquisition.snapshot = make_snapshot()


def test_rejects_invalid_snapshot():
    from app.adapters.mediamtx.metrics_acquisition import (
        MediaMTXMetricsAcquisition,
    )

    with pytest.raises(TypeError):
        MediaMTXMetricsAcquisition(
            snapshot="invalid",
            interval=make_interval(),
        )


def test_rejects_invalid_interval():
    from app.adapters.mediamtx.metrics_acquisition import (
        MediaMTXMetricsAcquisition,
    )

    with pytest.raises(TypeError):
        MediaMTXMetricsAcquisition(
            snapshot=make_snapshot(),
            interval="invalid",
        )


def test_does_not_perform_http():
    from app.adapters.mediamtx.metrics_acquisition import (
        MediaMTXMetricsAcquisition,
    )

    acquisition = MediaMTXMetricsAcquisition(
        snapshot=make_snapshot(),
        interval=make_interval(),
    )

    assert acquisition.snapshot.find(
        "srt_conns_ms_rtt",
        path="ejtv",
    )


def test_preserves_acquisition_source():
    from app.adapters.mediamtx.metrics_acquisition import (
        MediaMTXMetricsAcquisition,
    )

    acquisition = MediaMTXMetricsAcquisition(
        snapshot=make_snapshot(),
        interval=make_interval(),
    )

    assert acquisition.interval.source == "mediamtx.metrics"
