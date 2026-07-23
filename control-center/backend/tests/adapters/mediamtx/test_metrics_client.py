"""Pruebas del cliente de métricas MediaMTX."""

from __future__ import annotations

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


class FakeHttpClient:
    """Doble HTTP configurable para el servidor de métricas."""

    base_url = "http://127.0.0.1:9998"

    def __init__(
        self,
        *,
        body: bytes = b"",
        error: Exception | None = None,
    ) -> None:
        self.body = body
        self.error = error
        self.requested_path: str | None = None
        self.requested_headers: dict[str, str] | None = None

    def get(
        self,
        path: str,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        self.requested_path = path
        self.requested_headers = headers

        if self.error is not None:
            raise self.error

        return HttpResponse(
            status_code=200,
            headers={
                "Content-Type": "text/plain; version=0.0.4",
            },
            body=self.body,
        )


def test_get_metrics_text_returns_payload() -> None:
    body = (
        b'paths{name="enlace",state="ready"} 1\n'
        b'paths_inbound_bytes{name="enlace",state="ready"} 1000\n'
    )

    http = FakeHttpClient(body=body)
    client = MediaMTXMetricsClient(http)  # type: ignore[arg-type]

    result = client.get_metrics_text()

    assert result == body.decode("utf-8")
    assert http.requested_path == "/metrics"
    assert http.requested_headers == {
        "Accept": "text/plain",
    }


def test_health_is_true_when_metrics_respond() -> None:
    http = FakeHttpClient(body=b"paths 2\n")
    client = MediaMTXMetricsClient(http)  # type: ignore[arg-type]

    assert client.health() is True


def test_empty_metrics_response_is_rejected() -> None:
    http = FakeHttpClient(body=b"   \n")
    client = MediaMTXMetricsClient(http)  # type: ignore[arg-type]

    with pytest.raises(MediaMTXInvalidResponseError):
        client.get_metrics_text()


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
def test_http_errors_are_translated(
    http_error: Exception,
    expected_error: type[Exception],
) -> None:
    http = FakeHttpClient(error=http_error)
    client = MediaMTXMetricsClient(http)  # type: ignore[arg-type]

    with pytest.raises(expected_error):
        client.get_metrics_text()


def test_health_is_false_when_metrics_fail() -> None:
    http = FakeHttpClient(
        error=HttpConnectionError("connection refused")
    )
    client = MediaMTXMetricsClient(http)  # type: ignore[arg-type]

    assert client.health() is False
