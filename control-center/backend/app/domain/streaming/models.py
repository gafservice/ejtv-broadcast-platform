"""Modelos del dominio para monitoreo de servidores multimedia."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class MediaPathStatus(StrEnum):
    """Estado operativo normalizado de un path multimedia."""

    ACTIVE = "ACTIVE"
    NO_SOURCE = "NO_SOURCE"
    OFFLINE = "OFFLINE"


@dataclass(frozen=True, slots=True)
class MediaSource:
    """Fuente que publica contenido sobre un path."""

    source_type: str
    source_id: str | None = None


@dataclass(frozen=True, slots=True)
class MediaReader:
    """Cliente que consume un path multimedia."""

    reader_type: str
    reader_id: str | None = None


@dataclass(frozen=True, slots=True)
class MediaTrack:
    """Pista de audio, video o datos transportada por un path."""

    codec: str
    properties: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MediaPath:
    """Representación normalizada de un path multimedia."""

    name: str
    configuration_name: str
    status: MediaPathStatus

    ready: bool
    available: bool
    online: bool

    ready_time: datetime | None = None
    available_time: datetime | None = None
    online_time: datetime | None = None

    source: MediaSource | None = None
    tracks: tuple[MediaTrack, ...] = ()
    readers: tuple[MediaReader, ...] = ()

    inbound_bytes: int = 0
    outbound_bytes: int = 0
    inbound_frames_in_error: int = 0

    @property
    def reader_count(self) -> int:
        """Cantidad de lectores actualmente conectados."""
        return len(self.readers)

    @property
    def track_count(self) -> int:
        """Cantidad de pistas disponibles."""
        return len(self.tracks)

    @property
    def has_source(self) -> bool:
        """Indica si el path posee una fuente identificada."""
        return self.source is not None

    @property
    def is_active(self) -> bool:
        """Indica si el path se encuentra operativo."""
        return self.status is MediaPathStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class MediaMTXSnapshot:
    """Estado normalizado de MediaMTX en un instante determinado."""

    captured_at: datetime
    paths: tuple[MediaPath, ...]
    reported_item_count: int
    reported_page_count: int

    @classmethod
    def empty(cls) -> "MediaMTXSnapshot":
        """Construye un snapshot válido sin paths."""
        return cls(
            captured_at=datetime.now(timezone.utc),
            paths=(),
            reported_item_count=0,
            reported_page_count=0,
        )

    @property
    def path_count(self) -> int:
        """Cantidad real de paths contenidos en el snapshot."""
        return len(self.paths)

    @property
    def active_path_count(self) -> int:
        """Cantidad de paths activos."""
        return sum(path.is_active for path in self.paths)

    @property
    def total_reader_count(self) -> int:
        """Cantidad total de lectores en todos los paths."""
        return sum(path.reader_count for path in self.paths)

    def get_path(self, name: str) -> MediaPath | None:
        """Busca un path por su nombre."""
        return next(
            (path for path in self.paths if path.name == name),
            None,
        )
