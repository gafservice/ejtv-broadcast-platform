"""Cliente HTTP síncrono y reutilizable para adaptadores externos."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class HttpClientError(Exception):
    """Error base del cliente HTTP."""


class HttpConnectionError(HttpClientError):
    """No fue posible establecer comunicación con el servidor."""


class HttpTimeoutError(HttpClientError):
    """La operación HTTP excedió el tiempo permitido."""


class HttpStatusError(HttpClientError):
    """El servidor respondió con un código HTTP no exitoso."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message


class HttpInvalidResponseError(HttpClientError):
    """La respuesta recibida no contiene JSON válido."""


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """Respuesta HTTP normalizada."""

    status_code: int
    headers: Mapping[str, str]
    body: bytes

    def json(self) -> Any:
        """Decodifica el cuerpo como JSON."""
        try:
            return json.loads(self.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HttpInvalidResponseError(
                "La respuesta no contiene JSON válido."
            ) from exc


class HttpClient:
    """Cliente HTTP básico basado únicamente en la biblioteca estándar."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 5.0,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout debe ser mayor que cero.")

        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._default_headers = {
            "Accept": "application/json",
            **dict(default_headers or {}),
        }

    @property
    def base_url(self) -> str:
        """Dirección base configurada."""
        return self._base_url

    @property
    def timeout(self) -> float:
        """Tiempo máximo de espera configurado."""
        return self._timeout

    def get(
        self,
        path: str,
        headers: Mapping[str, str] | None = None,
    ) -> HttpResponse:
        """Ejecuta una solicitud HTTP GET."""
        return self.request("GET", path, headers=headers)

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: Mapping[str, str] | None = None,
        body: bytes | None = None,
    ) -> HttpResponse:
        """Ejecuta una solicitud HTTP."""
        url = self._build_url(path)
        request_headers = {
            **self._default_headers,
            **dict(headers or {}),
        }

        request = Request(
            url=url,
            data=body,
            headers=request_headers,
            method=method.upper(),
        )

        try:
            with urlopen(request, timeout=self._timeout) as response:
                return HttpResponse(
                    status_code=response.status,
                    headers=dict(response.headers.items()),
                    body=response.read(),
                )

        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise HttpStatusError(exc.code, error_body or exc.reason) from exc

        except TimeoutError as exc:
            raise HttpTimeoutError(
                f"Timeout consultando {url}."
            ) from exc

        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise HttpTimeoutError(
                    f"Timeout consultando {url}."
                ) from exc

            raise HttpConnectionError(
                f"No fue posible conectar con {url}: {exc.reason}"
            ) from exc

    def _build_url(self, path: str) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"{self._base_url}{normalized_path}"
