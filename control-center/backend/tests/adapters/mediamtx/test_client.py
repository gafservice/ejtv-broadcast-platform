"""Pruebas unitarias del cliente MediaMTX."""

from __future__ import annotations

import json

import pytest

from app.adapters.mediamtx.client import MediaMTXClient
from app.adapters.mediamtx.exceptions import (
    MediaMTXConnectionError,
    MediaMTXHTTPError,
    MediaMTXInvalidResponseError,
    MediaMTXTimeoutError,
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

        body = json.dumps(self.payload).encode("utf-8")

        return HttpResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=body,
        )


def test_get_paths_returns_mediamtx_payload() -> None:
    payload = {
        "itemCount": 1,
        "pageCount": 1,
        "items": [{"name": "enlace"}],
    }
    http = FakeHttpClient(payload=payload)
    client = MediaMTXClient(http)  # type: ignore[arg-type]

    result = client.get_paths()

    assert result == payload
    assert http.requested_path == "/v3/paths/list"


def test_get_paths_accepts_empty_items() -> None:
    http = FakeHttpClient(
        payload={
            "itemCount": 0,
            "pageCount": 0,
            "items": [],
        }
    )
    client = MediaMTXClient(http)  # type: ignore[arg-type]

    result = client.get_paths()

    assert result["items"] == []


def test_get_paths_rejects_non_object_response() -> None:
    http = FakeHttpClient(payload=[])
    client = MediaMTXClient(http)  # type: ignore[arg-type]

    with pytest.raises(MediaMTXInvalidResponseError):
        client.get_paths()


def test_get_paths_rejects_invalid_items() -> None:
    http = FakeHttpClient(payload={"items": "invalid"})
    client = MediaMTXClient(http)  # type: ignore[arg-type]

    with pytest.raises(MediaMTXInvalidResponseError):
        client.get_paths()


def test_connection_error_is_translated() -> None:
    http = FakeHttpClient(
        error=HttpConnectionError("connection refused")
    )
    client = MediaMTXClient(http)  # type: ignore[arg-type]

    with pytest.raises(MediaMTXConnectionError):
        client.get_paths()


def test_timeout_is_translated() -> None:
    http = FakeHttpClient(
        error=HttpTimeoutError("timeout")
    )
    client = MediaMTXClient(http)  # type: ignore[arg-type]

    with pytest.raises(MediaMTXTimeoutError):
        client.get_paths()


def test_http_error_is_translated() -> None:
    http = FakeHttpClient(
        error=HttpStatusError(500, "internal error")
    )
    client = MediaMTXClient(http)  # type: ignore[arg-type]

    with pytest.raises(MediaMTXHTTPError) as error:
        client.get_paths()

    assert error.value.status_code == 500


def test_health_is_true_when_api_responds() -> None:
    http = FakeHttpClient(payload={"items": []})
    client = MediaMTXClient(http)  # type: ignore[arg-type]

    assert client.health() is True


def test_health_is_false_when_api_fails() -> None:
    http = FakeHttpClient(
        error=HttpConnectionError("connection refused")
    )
    client = MediaMTXClient(http)  # type: ignore[arg-type]

    assert client.health() is False
