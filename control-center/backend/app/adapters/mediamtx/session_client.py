"""Cliente HTTP para los endpoints de sesiones de MediaMTX."""

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


class MediaMTXSessionClient:
    """Encapsula los endpoints HTTP de sesiones de MediaMTX."""

    SRT_CONNECTIONS_ENDPOINT = "/v3/srtconns/list"
    RTMP_CONNECTIONS_ENDPOINT = "/v3/rtmpconns/list"
    RTSP_CONNECTIONS_ENDPOINT = "/v3/rtspconns/list"
    RTSP_SESSIONS_ENDPOINT = "/v3/rtspsessions/list"
    HLS_SESSIONS_ENDPOINT = "/v3/hlssessions/list"
    WEBRTC_SESSIONS_ENDPOINT = "/v3/webrtcsessions/list"

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    @property
    def base_url(self) -> str:
        """Dirección base de la API de MediaMTX."""

        return self._http_client.base_url

    def get_srt_connections(self) -> dict[str, Any]:
        """Obtiene las conexiones SRT activas."""

        return self._get_collection(
            endpoint=self.SRT_CONNECTIONS_ENDPOINT,
            resource_name="conexiones SRT",
        )

    def get_rtmp_connections(self) -> dict[str, Any]:
        """Obtiene las conexiones RTMP activas."""

        return self._get_collection(
            endpoint=self.RTMP_CONNECTIONS_ENDPOINT,
            resource_name="conexiones RTMP",
        )

    def get_rtsp_connections(self) -> dict[str, Any]:
        """Obtiene las conexiones RTSP activas."""

        return self._get_collection(
            endpoint=self.RTSP_CONNECTIONS_ENDPOINT,
            resource_name="conexiones RTSP",
        )

    def get_rtsp_sessions(self) -> dict[str, Any]:
        """Obtiene las sesiones RTSP activas."""

        return self._get_collection(
            endpoint=self.RTSP_SESSIONS_ENDPOINT,
            resource_name="sesiones RTSP",
        )

    def get_hls_sessions(self) -> dict[str, Any]:
        """Obtiene las sesiones HLS activas."""

        return self._get_collection(
            endpoint=self.HLS_SESSIONS_ENDPOINT,
            resource_name="sesiones HLS",
        )

    def get_webrtc_sessions(self) -> dict[str, Any]:
        """Obtiene las sesiones WebRTC activas."""

        return self._get_collection(
            endpoint=self.WEBRTC_SESSIONS_ENDPOINT,
            resource_name="sesiones WebRTC",
        )

    def _get_collection(
        self,
        *,
        endpoint: str,
        resource_name: str,
    ) -> dict[str, Any]:
        """Obtiene y valida una colección JSON de MediaMTX."""

        try:
            response = self._http_client.get(endpoint)
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
                f"El endpoint de {resource_name} no devolvió "
                "un objeto JSON."
            )

        items = payload.get("items")

        if items is not None and not isinstance(items, list):
            raise MediaMTXInvalidResponseError(
                f"El campo 'items' de {resource_name} "
                "debe contener una lista."
            )

        return payload
