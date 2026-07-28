"""Pruebas unitarias del adaptador MediaMTX."""

from __future__ import annotations

import pytest

from app.adapters.mediamtx import MediaMTXAdapter
from app.adapters.mediamtx.exceptions import (
    MediaMTXInvalidResponseError,
)
from app.domain.streaming import MediaPathStatus


class FakeMediaMTXClient:
    """Cliente simulado para pruebas del adaptador."""

    def __init__(
        self,
        payload: dict[str, object],
        healthy: bool = True,
    ) -> None:
        self.payload = payload
        self.healthy = healthy

    def health(self) -> bool:
        return self.healthy

    def get_paths(self) -> dict[str, object]:
        return self.payload


def build_active_payload() -> dict[str, object]:
    return {
        "itemCount": 1,
        "pageCount": 1,
        "items": [
            {
                "name": "enlace",
                "confName": "enlace",
                "ready": True,
                "readyTime": (
                    "2026-07-10T16:18:58.778238962-06:00"
                ),
                "available": True,
                "availableTime": (
                    "2026-07-10T16:18:58.778238962-06:00"
                ),
                "online": True,
                "onlineTime": (
                    "2026-07-10T16:18:58.778239371-06:00"
                ),
                "source": {
                    "type": "mpegtsSource",
                    "id": "",
                },
                "tracks2": [
                    {
                        "codec": "MPEG-4 Audio",
                        "codecProps": {
                            "sampleRate": 48000,
                            "channelCount": 2,
                        },
                    },
                    {
                        "codec": "H265",
                        "codecProps": {
                            "width": 1920,
                            "height": 1080,
                            "profile": "Main",
                            "level": "4",
                        },
                    },
                ],
                "readers": [
                    {
                        "type": "srtConn",
                        "id": "reader-1",
                    }
                ],
                "inboundBytes": 1000,
                "outboundBytes": 2000,
                "inboundFramesInError": 0,
            }
        ],
    }


def test_adapter_builds_snapshot() -> None:
    client = FakeMediaMTXClient(build_active_payload())
    adapter = MediaMTXAdapter(client)  # type: ignore[arg-type]

    snapshot = adapter.get_snapshot()

    assert snapshot.path_count == 1
    assert snapshot.active_path_count == 1
    assert snapshot.total_reader_count == 1

    path = snapshot.get_path("enlace")

    assert path is not None
    assert path.status is MediaPathStatus.ACTIVE
    assert path.source is not None
    assert path.source.source_type == "mpegtsSource"
    assert path.track_count == 2
    assert path.tracks[1].codec == "H265"
    assert path.tracks[1].properties["width"] == 1920
    assert path.inbound_bytes == 1000
    assert path.outbound_bytes == 2000


def test_adapter_supports_empty_snapshot() -> None:
    client = FakeMediaMTXClient(
        {
            "itemCount": 0,
            "pageCount": 0,
            "items": [],
        }
    )
    adapter = MediaMTXAdapter(client)  # type: ignore[arg-type]

    snapshot = adapter.get_snapshot()

    assert snapshot.path_count == 0


def test_adapter_classifies_path_without_source() -> None:
    client = FakeMediaMTXClient(
        {
            "itemCount": 1,
            "pageCount": 1,
            "items": [
                {
                    "name": "backup",
                    "ready": False,
                    "available": False,
                    "online": False,
                    "source": None,
                    "tracks": [],
                    "readers": [],
                }
            ],
        }
    )
    adapter = MediaMTXAdapter(client)  # type: ignore[arg-type]

    snapshot = adapter.get_snapshot()
    path = snapshot.get_path("backup")

    assert path is not None
    assert path.status is MediaPathStatus.NO_SOURCE


def test_adapter_rejects_path_without_name() -> None:
    client = FakeMediaMTXClient(
        {
            "items": [
                {
                    "ready": True,
                }
            ]
        }
    )
    adapter = MediaMTXAdapter(client)  # type: ignore[arg-type]

    with pytest.raises(MediaMTXInvalidResponseError):
        adapter.get_snapshot()


def test_adapter_rejects_invalid_reader() -> None:
    payload = build_active_payload()
    items = payload["items"]
    assert isinstance(items, list)

    item = items[0]
    assert isinstance(item, dict)

    item["readers"] = ["invalid"]

    adapter = MediaMTXAdapter(
        FakeMediaMTXClient(payload)  # type: ignore[arg-type]
    )

    with pytest.raises(MediaMTXInvalidResponseError):
        adapter.get_snapshot()


def test_adapter_preserves_mediamtx_timezone() -> None:
    adapter = MediaMTXAdapter(
        FakeMediaMTXClient(
            build_active_payload()
        )  # type: ignore[arg-type]
    )

    path = adapter.get_snapshot().paths[0]

    assert path.ready_time is not None
    assert path.ready_time.utcoffset() is not None
    assert path.ready_time.utcoffset().total_seconds() == -21600


def test_health_delegates_to_client() -> None:
    adapter = MediaMTXAdapter(
        FakeMediaMTXClient(
            payload={"items": []},
            healthy=False,
        )  # type: ignore[arg-type]
    )

    assert adapter.health() is False
