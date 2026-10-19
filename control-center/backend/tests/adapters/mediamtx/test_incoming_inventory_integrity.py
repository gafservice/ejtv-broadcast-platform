"""Contract tests for trustworthy MediaMTX incoming inventories."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from app.adapters.mediamtx.adapter import MediaMTXAdapter
from app.adapters.mediamtx.exceptions import MediaMTXInvalidResponseError


def build_adapter(payload: dict[str, object]) -> MediaMTXAdapter:
    client = Mock()
    client.get_paths.return_value = payload
    return MediaMTXAdapter(client)


def test_missing_items_cannot_be_treated_as_empty_inventory() -> None:
    adapter = build_adapter(
        {
            "itemCount": 0,
            "pageCount": 0,
        }
    )

    with pytest.raises(MediaMTXInvalidResponseError):
        adapter.get_snapshot()


def test_multiple_pages_cannot_be_silently_accepted_as_complete() -> None:
    adapter = build_adapter(
        {
            "itemCount": 25,
            "pageCount": 3,
            "items": [
                {
                    "name": "ejtv",
                    "ready": True,
                    "available": True,
                    "online": True,
                    "source": {
                        "type": "mpegtsSource",
                        "id": "",
                    },
                    "inboundBytes": 1000,
                    "outboundBytes": 0,
                }
            ],
        }
    )

    with pytest.raises(MediaMTXInvalidResponseError):
        adapter.get_snapshot()


def test_complete_single_page_inventory_remains_supported() -> None:
    adapter = build_adapter(
        {
            "itemCount": 1,
            "pageCount": 1,
            "items": [
                {
                    "name": "ejtv",
                    "ready": True,
                    "available": True,
                    "online": True,
                    "source": {
                        "type": "mpegtsSource",
                        "id": "",
                    },
                    "inboundBytes": 1000,
                    "outboundBytes": 0,
                }
            ],
        }
    )

    snapshot = adapter.get_snapshot()

    assert snapshot.path_count == 1
    assert snapshot.reported_item_count == 1
    assert snapshot.reported_page_count == 1
    assert snapshot.paths[0].name == "ejtv"
