"""Pruebas del adaptador de sesiones MediaMTX."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from app.adapters.mediamtx.exceptions import (
    MediaMTXInvalidResponseError,
)
from app.adapters.mediamtx.session_adapter import (
    MediaMTXSessionAdapter,
)
from app.domain.sessions import (
    SessionProtocol,
    SessionQuality,
    SessionRole,
)


def build_srt_item(
    *,
    session_id: str = "44479f47-6533-4930-b986-180a95fb8255",
    state: str = "read",
    remote_addr: str = "201.192.154.132:21520",
) -> dict[str, object]:
    """Construye una conexión SRT similar a la API real."""

    return {
        "id": session_id,
        "created": "2026-07-24T12:00:00.000000Z",
        "remoteAddr": remote_addr,
        "state": state,
        "path": "enlace",
        "query": "",
        "user": "",
        "bytesReceived": 0,
        "bytesSent": 2_980_118_536,
        "packetsReceived": 0,
        "packetsSent": 2_309_449,
        "packetsLost": 29_909,
        "packetsRetransmitted": 23_026,
        "msRTT": 6.96,
        "mbpsReceiveRate": 0.0,
        "mbpsSendRate": 3.97,
        "mbpsLinkCapacity": 20.53,
    }


def build_adapter(
    payload: object,
) -> tuple[MediaMTXSessionAdapter, Mock]:
    """Construye el adaptador con un cliente simulado."""

    client = Mock()
    client.get_srt_connections.return_value = payload

    return MediaMTXSessionAdapter(client), client


def test_get_srt_snapshot_normalizes_connection() -> None:
    adapter, client = build_adapter(
        {
            "itemCount": 1,
            "pageCount": 1,
            "items": [build_srt_item()],
        }
    )

    snapshot = adapter.get_srt_snapshot()

    client.get_srt_connections.assert_called_once_with()

    assert snapshot.session_count == 1
    assert snapshot.reader_count == 1
    assert snapshot.publisher_count == 0

    session = snapshot.sessions[0]

    assert (
        session.session_id
        == "44479f47-6533-4930-b986-180a95fb8255"
    )
    assert session.protocol is SessionProtocol.SRT
    assert session.role is SessionRole.READER
    assert session.remote_ip == "201.192.154.132"
    assert session.remote_port == 21520
    assert session.path == "enlace"
    assert session.username is None
    assert session.bytes_sent == 2_980_118_536
    assert session.packets_sent == 2_309_449
    assert session.packets_lost == 29_909
    assert session.packets_retransmitted == 23_026
    assert session.rtt_ms == 6.96
    assert session.bitrate_send_mbps == 3.97
    assert session.link_capacity_mbps == 20.53
    assert session.packet_loss_rate == pytest.approx(
        1.2951,
        rel=1e-3,
    )
    assert session.retransmission_rate == pytest.approx(
        0.997,
        rel=1e-3,
    )
    assert session.quality is SessionQuality.FAIR


def test_publish_state_becomes_publisher() -> None:
    item = build_srt_item(
        state="publish",
        remote_addr="190.115.202.229:55000",
    )
    item.update(
        {
            "packetsReceived": 100_000,
            "packetsSent": 0,
            "packetsLost": 100,
            "mbpsReceiveRate": 4.5,
            "mbpsSendRate": 0.0,
        }
    )

    adapter, _ = build_adapter(
        {
            "items": [item],
        }
    )

    session = adapter.get_srt_snapshot().sessions[0]

    assert session.role is SessionRole.PUBLISHER
    assert session.effective_bitrate_mbps == 4.5
    assert session.packet_loss_rate == pytest.approx(
        100 * 100 / 100_100
    )


def test_unknown_state_becomes_unknown_role() -> None:
    adapter, _ = build_adapter(
        {
            "items": [
                build_srt_item(state="idle"),
            ],
        }
    )

    session = adapter.get_srt_snapshot().sessions[0]

    assert session.role is SessionRole.UNKNOWN


def test_empty_collection_returns_empty_snapshot() -> None:
    adapter, _ = build_adapter(
        {
            "itemCount": 0,
            "pageCount": 0,
            "items": [],
        }
    )

    snapshot = adapter.get_srt_snapshot()

    assert snapshot.session_count == 0
    assert snapshot.sessions == ()


def test_missing_items_is_treated_as_empty_collection() -> None:
    adapter, _ = build_adapter({})

    snapshot = adapter.get_srt_snapshot()

    assert snapshot.session_count == 0


def test_invalid_collection_item_is_rejected() -> None:
    adapter, _ = build_adapter(
        {
            "items": [
                build_srt_item(),
                "invalid",
            ],
        }
    )

    with pytest.raises(MediaMTXInvalidResponseError):
        adapter.get_srt_snapshot()


@pytest.mark.parametrize(
    "missing_field",
    [
        "id",
        "created",
        "remoteAddr",
    ],
)
def test_required_fields_are_validated(
    missing_field: str,
) -> None:
    item = build_srt_item()
    item.pop(missing_field)

    adapter, _ = build_adapter(
        {
            "items": [item],
        }
    )

    with pytest.raises(MediaMTXInvalidResponseError):
        adapter.get_srt_snapshot()


@pytest.mark.parametrize(
    "remote_address",
    [
        "",
        "201.192.154.132:not-a-port",
        "201.192.154.132:0",
        "201.192.154.132:65536",
        "[2001:db8::10",
    ],
)
def test_invalid_remote_address_is_rejected(
    remote_address: str,
) -> None:
    adapter, _ = build_adapter(
        {
            "items": [
                build_srt_item(
                    remote_addr=remote_address,
                ),
            ],
        }
    )

    with pytest.raises(MediaMTXInvalidResponseError):
        adapter.get_srt_snapshot()


def test_ipv6_remote_address_is_supported() -> None:
    adapter, _ = build_adapter(
        {
            "items": [
                build_srt_item(
                    remote_addr="[2001:db8::10]:8890",
                ),
            ],
        }
    )

    session = adapter.get_srt_snapshot().sessions[0]

    assert session.remote_ip == "2001:db8::10"
    assert session.remote_port == 8890


def test_invalid_metric_values_do_not_break_snapshot() -> None:
    item = build_srt_item()
    item.update(
        {
            "bytesSent": "invalid",
            "packetsSent": None,
            "msRTT": "invalid",
            "mbpsSendRate": -10,
        }
    )

    adapter, _ = build_adapter(
        {
            "items": [item],
        }
    )

    session = adapter.get_srt_snapshot().sessions[0]

    assert session.bytes_sent == 0
    assert session.packets_sent == 0
    assert session.rtt_ms is None
    assert session.bitrate_send_mbps is None


def test_get_snapshot_delegates_to_srt_snapshot() -> None:
    """El punto genérico debe usar inicialmente el snapshot SRT."""

    client = Mock()
    client.get_srt_connections.return_value = {"items": []}

    adapter = MediaMTXSessionAdapter(client)

    snapshot = adapter.get_snapshot()

    assert snapshot.sessions == ()
    client.get_srt_connections.assert_called_once_with()
