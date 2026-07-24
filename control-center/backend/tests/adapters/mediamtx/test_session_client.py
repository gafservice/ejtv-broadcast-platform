"""Pruebas unitarias del cliente de sesiones MediaMTX."""

from __future__ import annotations

import json

import pytest

from app.adapters.mediamtx.exceptions import (
    MediaMTXConnectionError,
    MediaMTXHTTPError,
    MediaMTXInvalidResponseError,
    MediaMTXTimeoutError,
)
from app.adapters.mediamtx.session_client import (
    MediaMTXSessionClient,
)
from app.core.http import (
    HttpConnectionError,
    HttpResponse,
    HttpStatusError,
    HttpTimeoutError,
)


class FakeHttpClient:
    """Doble de prueba configurable."""

    base_url = "http://127.0.0.1:9997"

    def __init__(
        self,
        payload: object | None = None,
        error: Exception | None = None,
    ) -> None:
        self.payload = payload
        self.error = error
        self.requested_path: str | None = None

    def get(self, path: str) -> HttpResponse:
        self.requested_path = path

        if self.error is not None:
            raise self.error

        return HttpResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=json.dumps(self.payload).encode("utf-8"),
        )


@pytest.mark.parametrize(
    ("method_name", "expected_endpoint"),
    [
        (
            "get_srt_connections",
            "/v3/srtconns/list",
        ),
        (
            "get_rtmp_connections",
            "/v3/rtmpconns/list",
        ),
        (
            "get_rtsp_connections",
            "/v3/rtspconns/list",
        ),
        (
            "get_rtsp_sessions",
            "/v3/rtspsessions/list",
        ),
        (
            "get_hls_sessions",
            "/v3/hlssessions/list",
        ),
        (
            "get_webrtc_sessions",
            "/v3/webrtcsessions/list",
        ),
    ],
)
def test_session_endpoints_return_payload(
    method_name: str,
    expected_endpoint: str,
) -> None:
    payload = {
        "itemCount": 1,
        "pageCount": 1,
        "items": [{"id": "session-001"}],
    }
    http = FakeHttpClient(payload=payload)
    client = MediaMTXSessionClient(http)  # type: ignore[arg-type]

    method = getattr(client, method_name)
    result = method()

    assert result == payload
    assert http.requested_path == expected_endpoint


def test_session_endpoint_accepts_empty_items() -> None:
    http = FakeHttpClient(
        payload={
            "itemCount": 0,
            "pageCount": 0,
            "items": [],
        }
    )
    client = MediaMTXSessionClient(http)  # type: ignore[arg-type]

    result = client.get_srt_connections()

    assert result["items"] == []


def test_session_endpoint_rejects_non_object_response() -> None:
    http = FakeHttpClient(payload=[])
    client = MediaMTXSessionClient(http)  # type: ignore[arg-type]

    with pytest.raises(MediaMTXInvalidResponseError):
        client.get_srt_connections()


def test_session_endpoint_rejects_invalid_items() -> None:
    http = FakeHttpClient(payload={"items": "invalid"})
    client = MediaMTXSessionClient(http)  # type: ignore[arg-type]

    with pytest.raises(MediaMTXInvalidResponseError):
        client.get_srt_connections()


def test_session_connection_error_is_translated() -> None:
    http = FakeHttpClient(
        error=HttpConnectionError("connection refused")
    )
    client = MediaMTXSessionClient(http)  # type: ignore[arg-type]

    with pytest.raises(MediaMTXConnectionError):
        client.get_srt_connections()


def test_session_timeout_is_translated() -> None:
    http = FakeHttpClient(
        error=HttpTimeoutError("timeout")
    )
    client = MediaMTXSessionClient(http)  # type: ignore[arg-type]

    with pytest.raises(MediaMTXTimeoutError):
        client.get_srt_connections()


def test_session_http_error_is_translated() -> None:
    http = FakeHttpClient(
        error=HttpStatusError(500, "internal error")
    )
    client = MediaMTXSessionClient(http)  # type: ignore[arg-type]

    with pytest.raises(MediaMTXHTTPError) as error:
        client.get_srt_connections()

    assert error.value.status_code == 500
