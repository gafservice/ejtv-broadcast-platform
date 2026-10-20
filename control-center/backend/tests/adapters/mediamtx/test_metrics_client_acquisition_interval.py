"""Contract for timestamped MediaMTX metrics acquisition."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.adapters.mediamtx.exceptions import (
    MediaMTXConnectionError,
    MediaMTXHTTPError,
    MediaMTXInvalidResponseError,
    MediaMTXTimeoutError,
)
from app.adapters.mediamtx.metrics_client import (
    MediaMTXMetricsClient,
)
from app.core.http import (
    HttpConnectionError,
    HttpResponse,
    HttpStatusError,
    HttpTimeoutError,
)
from app.domain.streaming.evidence_acquisition_interval import (
    EvidenceAcquisitionInterval,
)


class RecordingHttpClient:
    """Record HTTP acquisition boundaries without network access."""

    base_url = "http://127.0.0.1:9998"

    def __init__(
        self,
        *,
        body: bytes = b"paths 2\n",
        error: Exception | None = None,
    ) -> None:
        self.body = body
        self.error = error
        self.calls = 0
        self.requested_path = None
        self.requested_headers = None
        self.entered_at = None
        self.returned_at = None

    def get(self, path, headers=None):
        self.calls += 1
        self.requested_path = path
        self.requested_headers = headers
        self.entered_at = datetime.now(UTC)

        if self.error is not None:
            raise self.error

        response = HttpResponse(
            status_code=200,
            headers={"Content-Type": "text/plain"},
            body=self.body,
        )

        self.returned_at = datetime.now(UTC)

        return response


def test_returns_original_metrics_text_and_interval():
    http = RecordingHttpClient(
        body=b'paths{name="ejtv",state="ready"} 1\n'
    )

    client = MediaMTXMetricsClient(http)

    text, interval = (
        client.get_metrics_with_acquisition_interval()
    )

    assert text == 'paths{name="ejtv",state="ready"} 1\n'
    assert isinstance(interval, EvidenceAcquisitionInterval)
    assert interval.source == "mediamtx.metrics"


def test_acquisition_interval_uses_utc():
    http = RecordingHttpClient()
    client = MediaMTXMetricsClient(http)

    _, interval = (
        client.get_metrics_with_acquisition_interval()
    )

    assert interval.started_at.utcoffset().total_seconds() == 0
    assert interval.completed_at.utcoffset().total_seconds() == 0
    assert interval.started_at <= interval.completed_at


def test_acquisition_interval_contains_http_request():
    http = RecordingHttpClient()
    client = MediaMTXMetricsClient(http)

    _, interval = (
        client.get_metrics_with_acquisition_interval()
    )

    assert http.entered_at is not None
    assert http.returned_at is not None

    assert interval.started_at <= http.entered_at
    assert interval.completed_at >= http.returned_at


def test_acquisition_uses_exactly_one_http_request():
    http = RecordingHttpClient()
    client = MediaMTXMetricsClient(http)

    client.get_metrics_with_acquisition_interval()

    assert http.calls == 1
    assert http.requested_path == "/metrics"
    assert http.requested_headers == {
        "Accept": "text/plain",
    }


def test_empty_response_is_rejected():
    http = RecordingHttpClient(body=b"  \n")
    client = MediaMTXMetricsClient(http)

    with pytest.raises(MediaMTXInvalidResponseError):
        client.get_metrics_with_acquisition_interval()

    assert http.calls == 1


@pytest.mark.parametrize(
    ("http_error", "expected_error"),
    [
        (
            HttpConnectionError("connection refused"),
            MediaMTXConnectionError,
        ),
        (
            HttpTimeoutError("timeout"),
            MediaMTXTimeoutError,
        ),
        (
            HttpStatusError(500, "internal error"),
            MediaMTXHTTPError,
        ),
    ],
)
def test_http_errors_preserve_translation(
    http_error,
    expected_error,
):
    http = RecordingHttpClient(error=http_error)
    client = MediaMTXMetricsClient(http)

    with pytest.raises(expected_error):
        client.get_metrics_with_acquisition_interval()

    assert http.calls == 1


def test_legacy_method_remains_compatible():
    http = RecordingHttpClient(body=b"paths 2\n")
    client = MediaMTXMetricsClient(http)

    assert client.get_metrics_text() == "paths 2\n"
    assert http.calls == 1
