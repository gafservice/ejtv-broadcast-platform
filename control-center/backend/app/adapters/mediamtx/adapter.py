"""Adaptador entre la API de MediaMTX y el dominio multimedia."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Mapping

from app.domain.streaming import (
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaReader,
    MediaSource,
    MediaTrack,
)

from .client import MediaMTXClient
from .exceptions import MediaMTXInvalidResponseError


class MediaMTXAdapter:
    """Transforma respuestas de MediaMTX en objetos del dominio."""

    def __init__(self, client: MediaMTXClient) -> None:
        self._client = client

    def health(self) -> bool:
        """Indica si la API de MediaMTX está disponible."""
        return self._client.health()

    def get_snapshot(self) -> MediaMTXSnapshot:
        """Obtiene el estado normalizado del servidor multimedia."""
        payload = self._client.get_paths()

        raw_items = payload.get("items", [])

        if not isinstance(raw_items, list):
            raise MediaMTXInvalidResponseError(
                "El campo 'items' debe ser una lista."
            )

        paths = tuple(
            self._parse_path(item)
            for item in raw_items
            if isinstance(item, Mapping)
        )

        if len(paths) != len(raw_items):
            raise MediaMTXInvalidResponseError(
                "Uno o más elementos de 'items' no son objetos válidos."
            )

        return MediaMTXSnapshot(
            captured_at=datetime.now(timezone.utc),
            paths=paths,
            reported_item_count=self._safe_int(
                payload.get("itemCount"),
                default=len(paths),
            ),
            reported_page_count=self._safe_int(
                payload.get("pageCount"),
                default=0,
            ),
        )

    def _parse_path(self, item: Mapping[str, Any]) -> MediaPath:
        name = self._required_string(item, "name")

        configuration_name = self._optional_string(
            item.get("confName")
        ) or name

        ready = self._safe_bool(item.get("ready"))
        available = self._safe_bool(item.get("available"))
        online = self._safe_bool(item.get("online"))

        return MediaPath(
            name=name,
            configuration_name=configuration_name,
            status=self._resolve_status(
                ready=ready,
                available=available,
                online=online,
                source=item.get("source"),
            ),
            ready=ready,
            available=available,
            online=online,
            ready_time=self._parse_datetime(item.get("readyTime")),
            available_time=self._parse_datetime(
                item.get("availableTime")
            ),
            online_time=self._parse_datetime(item.get("onlineTime")),
            source=self._parse_source(item.get("source")),
            tracks=self._parse_tracks(item),
            readers=self._parse_readers(item.get("readers")),
            inbound_bytes=self._safe_int(
                item.get("inboundBytes", item.get("bytesReceived")),
            ),
            outbound_bytes=self._safe_int(
                item.get("outboundBytes", item.get("bytesSent")),
            ),
            inbound_frames_in_error=self._safe_int(
                item.get("inboundFramesInError"),
            ),
        )

    @staticmethod
    def _resolve_status(
        *,
        ready: bool,
        available: bool,
        online: bool,
        source: object,
    ) -> MediaPathStatus:
        if ready and available and online:
            return MediaPathStatus.ACTIVE

        if source is None:
            return MediaPathStatus.NO_SOURCE

        return MediaPathStatus.OFFLINE

    @staticmethod
    def _parse_source(value: object) -> MediaSource | None:
        if not isinstance(value, Mapping):
            return None

        source_type = value.get("type")

        if not isinstance(source_type, str) or not source_type:
            return None

        source_id = value.get("id")

        return MediaSource(
            source_type=source_type,
            source_id=source_id if isinstance(source_id, str) else None,
        )

    @staticmethod
    def _parse_readers(value: object) -> tuple[MediaReader, ...]:
        if value is None:
            return ()

        if not isinstance(value, list):
            raise MediaMTXInvalidResponseError(
                "El campo 'readers' debe ser una lista."
            )

        readers: list[MediaReader] = []

        for raw_reader in value:
            if not isinstance(raw_reader, Mapping):
                raise MediaMTXInvalidResponseError(
                    "Se encontró un reader inválido."
                )

            reader_type = raw_reader.get("type")

            if not isinstance(reader_type, str) or not reader_type:
                raise MediaMTXInvalidResponseError(
                    "Un reader no contiene un tipo válido."
                )

            reader_id = raw_reader.get("id")

            readers.append(
                MediaReader(
                    reader_type=reader_type,
                    reader_id=(
                        reader_id
                        if isinstance(reader_id, str)
                        else None
                    ),
                )
            )

        return tuple(readers)

    @staticmethod
    def _parse_tracks(
        item: Mapping[str, Any],
    ) -> tuple[MediaTrack, ...]:
        detailed_tracks = item.get("tracks2")

        if isinstance(detailed_tracks, list):
            tracks: list[MediaTrack] = []

            for raw_track in detailed_tracks:
                if not isinstance(raw_track, Mapping):
                    raise MediaMTXInvalidResponseError(
                        "Se encontró una pista inválida."
                    )

                codec = raw_track.get("codec")

                if not isinstance(codec, str) or not codec:
                    raise MediaMTXInvalidResponseError(
                        "Una pista no contiene un codec válido."
                    )

                properties = raw_track.get("codecProps", {})

                if not isinstance(properties, Mapping):
                    properties = {}

                tracks.append(
                    MediaTrack(
                        codec=codec,
                        properties=dict(properties),
                    )
                )

            return tuple(tracks)

        simple_tracks = item.get("tracks", [])

        if not isinstance(simple_tracks, list):
            raise MediaMTXInvalidResponseError(
                "El campo 'tracks' debe ser una lista."
            )

        return tuple(
            MediaTrack(codec=track)
            for track in simple_tracks
            if isinstance(track, str)
        )

    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None

        normalized = value.strip()

        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"

        # MediaMTX puede utilizar nanosegundos. datetime acepta
        # microsegundos, por lo que se conservan seis decimales.
        normalized = re.sub(
            r"(\.\d{6})\d+(?=[+-]\d{2}:\d{2}$)",
            r"\1",
            normalized,
        )

        try:
            return datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise MediaMTXInvalidResponseError(
                f"Fecha inválida recibida desde MediaMTX: {value}"
            ) from exc

    @staticmethod
    def _required_string(
        item: Mapping[str, Any],
        field_name: str,
    ) -> str:
        value = item.get(field_name)

        if not isinstance(value, str) or not value:
            raise MediaMTXInvalidResponseError(
                f"El campo '{field_name}' es obligatorio."
            )

        return value

    @staticmethod
    def _optional_string(value: object) -> str | None:
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _safe_bool(value: object) -> bool:
        return value if isinstance(value, bool) else False

    @staticmethod
    def _safe_int(value: object, default: int = 0) -> int:
        if isinstance(value, bool):
            return default

        if isinstance(value, int):
            return max(value, 0)

        return default
