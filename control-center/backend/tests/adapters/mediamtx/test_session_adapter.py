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


def test_get_snapshot_aggregates_supported_protocols() -> None:
    """El snapshot genérico debe integrar SRT y RTSP."""

    client = Mock()
    client.get_srt_connections.return_value = {
        "items": []
    }
    client.get_rtsp_sessions.return_value = {
        "items": []
    }
    client.get_rtmp_connections.return_value = {
        "items": []
    }
    client.get_hls_sessions.return_value = {
        "items": []
    }

    adapter = MediaMTXSessionAdapter(client)

    snapshot = adapter.get_snapshot()

    assert snapshot.sessions == ()

    client.get_srt_connections.assert_called_once_with()
    client.get_rtsp_sessions.assert_called_once_with()
    client.get_rtmp_connections.assert_called_once_with()
    client.get_hls_sessions.assert_called_once_with()
    client.get_srt_connections.assert_called_once_with()


def build_rtsp_item(
    *,
    session_id: str = "rtsp-session-001",
    state: str = "read",
    path: str = "enlace",
) -> dict:
    """Construye una sesión RTSP similar a la API real."""

    return {
        "id": session_id,
        "created": "2026-08-21T17:30:32.096915047-06:00",
        "remoteAddr": "201.192.154.132:14577",
        "state": state,
        "path": path,
        "query": "",
        "user": "",
        "userAgent": (
            "LibVLC/3.0.23 "
            "(LIVE555 Streaming Media v2016.11.28)"
        ),
        "transport": "TCP",
        "profile": "AVP",
        "inboundBytes": 11480,
        "outboundBytes": 281063953,
        "bytesReceived": 11480,
        "bytesSent": 281063953,
        "rtpPacketsReceived": 0,
        "rtpPacketsSent": 216325,
        "rtpPacketsLost": 0,
    }


def test_get_rtsp_snapshot_normalizes_session() -> None:
    client = Mock()
    client.get_rtsp_sessions.return_value = {
        "items": [
            build_rtsp_item()
        ]
    }

    adapter = MediaMTXSessionAdapter(
        client=client,
    )

    snapshot = adapter.get_rtsp_snapshot()

    client.get_rtsp_sessions.assert_called_once_with()

    assert len(snapshot.sessions) == 1

    session = snapshot.sessions[0]

    assert session.session_id == "rtsp-session-001"
    assert session.protocol is SessionProtocol.RTSP
    assert session.role is SessionRole.READER
    assert session.state == "read"
    assert session.path == "enlace"
    assert session.remote_ip == "201.192.154.132"
    assert session.remote_port == 14577
    assert session.user_agent is not None


def test_get_snapshot_aggregates_srt_and_rtsp() -> None:
    client = Mock()

    client.get_srt_connections.return_value = {
        "items": [
            build_srt_item(
                session_id="srt-001",
            ),
            build_srt_item(
                session_id="srt-002",
            ),
        ]
    }

    client.get_rtsp_sessions.return_value = {
        "items": [
            build_rtsp_item(
                session_id="rtsp-001",
            ),
        ]
    }

    # El snapshot agregado ahora consulta también RTMP y HLS.
    # Para este test ambos protocolos permanecen vacíos.
    client.get_rtmp_connections.return_value = {
        "items": []
    }
    client.get_hls_sessions.return_value = {
        "items": []
    }

    adapter = MediaMTXSessionAdapter(
        client=client,
    )

    snapshot = adapter.get_snapshot()

    assert len(snapshot.sessions) == 3

    assert tuple(
        session.protocol
        for session in snapshot.sessions
    ) == (
        SessionProtocol.SRT,
        SessionProtocol.SRT,
        SessionProtocol.RTSP,
    )

    client.get_srt_connections.assert_called_once_with()
    client.get_rtsp_sessions.assert_called_once_with()
    client.get_rtmp_connections.assert_called_once_with()
    client.get_hls_sessions.assert_called_once_with()

def build_rtmp_item(
    *,
    session_id: str = "rtmp-001",
    state: str = "read",
    path: str = "enlace",
) -> dict:
    """Construye una conexión RTMP similar a la API real."""

    return {
        "id": session_id,
        "created": "2026-08-21T17:49:22.321362293-06:00",
        "remoteAddr": "201.192.154.132:15606",
        "state": state,
        "path": path,
        "query": "",
        "user": "",
        "userAgent": "LNX 9,0,124,2",
        "inboundBytes": 3443,
        "outboundBytes": 48726780,
        "bytesReceived": 3443,
        "bytesSent": 48726780,
    }


def build_hls_item(
    *,
    session_id: str = "hls-001",
    path: str = "ejtv",
) -> dict:
    """Construye una sesión HLS similar a la API real."""

    return {
        "id": session_id,
        "created": "2026-08-21T18:21:00.771169535-06:00",
        "remoteAddr": "201.192.154.132:17356",
        "path": path,
        "query": "",
        "user": "",
        "userAgent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64; rv:154.0)"
        ),
        "isCDN": False,
        "outboundBytes": 29803902,
    }


def test_get_rtmp_snapshot_normalizes_reader() -> None:
    client = Mock()

    client.get_rtmp_connections.return_value = {
        "items": [
            build_rtmp_item()
        ]
    }

    adapter = MediaMTXSessionAdapter(
        client=client,
    )

    snapshot = adapter.get_rtmp_snapshot()

    assert len(snapshot.sessions) == 1

    session = snapshot.sessions[0]

    assert session.protocol is SessionProtocol.RTMP
    assert session.role is SessionRole.READER
    assert session.state == "read"
    assert session.path == "enlace"
    assert session.remote_ip == "201.192.154.132"


def test_get_hls_snapshot_normalizes_reader() -> None:
    client = Mock()

    client.get_hls_sessions.return_value = {
        "items": [
            build_hls_item()
        ]
    }

    adapter = MediaMTXSessionAdapter(
        client=client,
    )

    snapshot = adapter.get_hls_snapshot()

    assert len(snapshot.sessions) == 1

    session = snapshot.sessions[0]

    assert session.protocol is SessionProtocol.HLS
    assert session.role is SessionRole.READER
    assert session.state == "read"
    assert session.path == "ejtv"
    assert session.remote_ip == "201.192.154.132"


def test_get_snapshot_aggregates_four_protocols() -> None:
    client = Mock()

    client.get_srt_connections.return_value = {
        "items": [
            build_srt_item(
                session_id="srt-001",
            )
        ]
    }

    client.get_rtsp_sessions.return_value = {
        "items": [
            build_rtsp_item(
                session_id="rtsp-001",
            )
        ]
    }

    client.get_rtmp_connections.return_value = {
        "items": [
            build_rtmp_item(
                session_id="rtmp-001",
            )
        ]
    }

    client.get_hls_sessions.return_value = {
        "items": [
            build_hls_item(
                session_id="hls-001",
            )
        ]
    }

    adapter = MediaMTXSessionAdapter(
        client=client,
    )

    snapshot = adapter.get_snapshot()

    assert len(snapshot.sessions) == 4

    assert tuple(
        session.protocol
        for session in snapshot.sessions
    ) == (
        SessionProtocol.SRT,
        SessionProtocol.RTSP,
        SessionProtocol.RTMP,
        SessionProtocol.HLS,
    )

    client.get_srt_connections.assert_called_once_with()
    client.get_rtsp_sessions.assert_called_once_with()
    client.get_rtmp_connections.assert_called_once_with()
    client.get_hls_sessions.assert_called_once_with()
