"""Cliente HTTP para las métricas Prometheus de MediaMTX."""

from __future__ import annotations

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


class MediaMTXMetricsClient:
    """Obtiene las métricas Prometheus expuestas por MediaMTX."""

    METRICS_ENDPOINT = "/metrics"

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    @property
    def base_url(self) -> str:
        """Dirección del servidor de métricas."""
        return self._http_client.base_url

    def health(self) -> bool:
        """Comprueba si el servidor de métricas responde."""
        try:
            self.get_metrics_text()
            return True
        except (
            MediaMTXConnectionError,
            MediaMTXTimeoutError,
            MediaMTXHTTPError,
            MediaMTXInvalidResponseError,
        ):
            return False

    def get_metrics_text(self) -> str:
        """Obtiene el documento Prometheus sin procesar."""
        try:
            response = self._http_client.get(
                self.METRICS_ENDPOINT,
                headers={
                    "Accept": "text/plain",
                },
            )
            metrics_text = response.text()

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

        if not metrics_text.strip():
            raise MediaMTXInvalidResponseError(
                "El endpoint /metrics devolvió una respuesta vacía."
            )

        return metrics_text
