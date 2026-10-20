"""RED contract for shared MediaMTX metrics acquisition service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from app.adapters.mediamtx.metrics_acquisition import (
    MediaMTXMetricsAcquisition,
)
from app.adapters.mediamtx.metrics_parser import (
    MediaMTXMetricsParser,
)
from app.domain.streaming.evidence_acquisition_interval import (
    EvidenceAcquisitionInterval,
)


STARTED_AT = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)

INTERVAL = EvidenceAcquisitionInterval(
    started_at=STARTED_AT,
    completed_at=STARTED_AT + timedelta(milliseconds=50),
    source="mediamtx.metrics",
)

METRICS_TEXT = (
    'srt_conns_ms_rtt'
    '{id="conn-1",path="ejtv",state="read"} 12.5'
)


def make_service():
    from app.services.mediamtx_metrics_acquisition_service import (
        MediaMTXMetricsAcquisitionService,
    )

    client = Mock()
    client.get_metrics_with_acquisition_interval.return_value = (
        METRICS_TEXT,
        INTERVAL,
    )

    parser = Mock(spec=MediaMTXMetricsParser)
    parser.parse.return_value = (
        MediaMTXMetricsParser().parse(METRICS_TEXT)
    )

    service = MediaMTXMetricsAcquisitionService(
        metrics_client=client,
        metrics_parser=parser,
    )

    return service, client, parser


def test_returns_typed_acquisition():
    service, _, _ = make_service()

    result = service.acquire()

    assert isinstance(result, MediaMTXMetricsAcquisition)


def test_performs_one_temporal_http_acquisition():
    service, client, _ = make_service()

    service.acquire()

    client.get_metrics_with_acquisition_interval.assert_called_once_with()
    client.get_metrics_text.assert_not_called()


def test_parses_metrics_exactly_once():
    service, _, parser = make_service()

    service.acquire()

    parser.parse.assert_called_once_with(METRICS_TEXT)


def test_preserves_snapshot_identity():
    service, _, parser = make_service()

    result = service.acquire()

    assert result.snapshot is parser.parse.return_value


def test_preserves_interval_identity():
    service, _, _ = make_service()

    result = service.acquire()

    assert result.interval is INTERVAL


def test_propagates_acquisition_failure():
    service, client, parser = make_service()

    client.get_metrics_with_acquisition_interval.side_effect = (
        RuntimeError("metrics unavailable")
    )

    with pytest.raises(RuntimeError, match="metrics unavailable"):
        service.acquire()

    parser.parse.assert_not_called()


def test_propagates_parser_failure():
    service, client, parser = make_service()

    parser.parse.side_effect = ValueError("invalid metrics")

    with pytest.raises(ValueError, match="invalid metrics"):
        service.acquire()

    client.get_metrics_with_acquisition_interval.assert_called_once_with()


def test_acquisition_does_not_cache_between_calls():
    service, client, parser = make_service()

    first = service.acquire()
    second = service.acquire()

    assert first is not second
    assert client.get_metrics_with_acquisition_interval.call_count == 2
    assert parser.parse.call_count == 2


def test_does_not_call_legacy_metrics_method():
    service, client, _ = make_service()

    service.acquire()

    client.get_metrics_text.assert_not_called()
