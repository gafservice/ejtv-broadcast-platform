"""Cliente de bajo nivel para la API HTTP de MediaMTX."""

from __future__ import annotations

from typing import Any

from app.core.http import (
    HttpClient,
    HttpConnectionError,
    HttpInvalidResponseError,
    HttpStatusError,
    HttpTimeoutError,
)

from .exceptions import (
    MediaMTXConnectionError,
    MediaMTXHTTPError,
    MediaMTXInvalidResponseError,
    MediaMTXTimeoutError,
)


class MediaMTXClient:
    """Encapsula los endpoints HTTP utilizados de MediaMTX."""

    PATHS_ENDPOINT = "/v3/paths/list"

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    @property
    def base_url(self) -> str:
        """Dirección de la API de MediaMTX."""
        return self._http_client.base_url

    def health(self) -> bool:
        """Comprueba si la API responde correctamente."""
        try:
            self.get_paths()
            return True
        except (
            MediaMTXConnectionError,
            MediaMTXTimeoutError,
            MediaMTXHTTPError,
            MediaMTXInvalidResponseError,
        ):
            return False

    def get_paths(self) -> dict[str, Any]:
        """Obtiene la respuesta cruda del endpoint de paths."""
        try:
            response = self._http_client.get(self.PATHS_ENDPOINT)
            payload = response.json()

        except HttpTimeoutError as exc:
            raise MediaMTXTimeoutError(str(exc)) from exc

        except HttpConnectionError as exc:
            raise MediaMTXConnectionError(str(exc)) from exc

        except HttpStatusError as exc:
            raise MediaMTXHTTPError(
                status_code=exc.status_code,
                message=exc.message,
            ) from exc

        except HttpInvalidResponseError as exc:
            raise MediaMTXInvalidResponseError(str(exc)) from exc

        if not isinstance(payload, dict):
            raise MediaMTXInvalidResponseError(
                "El endpoint de paths no devolvió un objeto JSON."
            )

        items = payload.get("items")

        if items is not None and not isinstance(items, list):
            raise MediaMTXInvalidResponseError(
                "El campo 'items' debe contener una lista."
            )

        return payload
