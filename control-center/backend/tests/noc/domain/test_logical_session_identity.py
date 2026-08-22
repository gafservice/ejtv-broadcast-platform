from datetime import UTC, datetime

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.logical_session_identity import (
    LogicalSessionIdentity,
)


NOW = datetime(
    2026,
    8,
    23,
    1,
    0,
    tzinfo=UTC,
)


def build_session(
    *,
    session_id: str = "session-001",
    protocol: SessionProtocol = SessionProtocol.SRT,
    role: SessionRole = SessionRole.READER,
    path: str | None = "ejtv",
    remote_ip: str = "201.192.154.132",
    remote_port: int = 50000,
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=protocol,
        role=role,
        state="read",
        remote_ip=remote_ip,
        remote_port=remote_port,
        path=path,
        connected_since=NOW,
    )


def test_identity_from_session() -> None:
    identity = LogicalSessionIdentity.from_session(
        build_session()
    )

    assert identity.protocol is SessionProtocol.SRT
    assert identity.role is SessionRole.READER
    assert identity.path == "ejtv"
    assert identity.remote_ip == "201.192.154.132"


def test_session_id_is_not_part_of_logical_identity() -> None:
    first = LogicalSessionIdentity.from_session(
        build_session(
            session_id="old-session",
        )
    )

    second = LogicalSessionIdentity.from_session(
        build_session(
            session_id="new-session",
        )
    )

    assert first == second


def test_remote_port_is_not_part_of_logical_identity() -> None:
    first = LogicalSessionIdentity.from_session(
        build_session(
            remote_port=50000,
        )
    )

    second = LogicalSessionIdentity.from_session(
        build_session(
            remote_port=51783,
        )
    )

    assert first == second


def test_remote_ip_is_part_of_logical_identity() -> None:
    first = LogicalSessionIdentity.from_session(
        build_session(
            remote_ip="201.192.154.132",
        )
    )

    second = LogicalSessionIdentity.from_session(
        build_session(
            remote_ip="190.10.20.30",
        )
    )

    assert first != second


def test_protocol_is_part_of_logical_identity() -> None:
    first = LogicalSessionIdentity.from_session(
        build_session(
            protocol=SessionProtocol.SRT,
        )
    )

    second = LogicalSessionIdentity.from_session(
        build_session(
            protocol=SessionProtocol.RTSP,
        )
    )

    assert first != second


def test_role_is_part_of_logical_identity() -> None:
    first = LogicalSessionIdentity.from_session(
        build_session(
            role=SessionRole.READER,
        )
    )

    second = LogicalSessionIdentity.from_session(
        build_session(
            role=SessionRole.PUBLISHER,
        )
    )

    assert first != second


def test_path_is_part_of_logical_identity() -> None:
    first = LogicalSessionIdentity.from_session(
        build_session(
            path="ejtv",
        )
    )

    second = LogicalSessionIdentity.from_session(
        build_session(
            path="enlace",
        )
    )

    assert first != second


def test_none_path_is_supported() -> None:
    identity = LogicalSessionIdentity.from_session(
        build_session(
            path=None,
        )
    )

    assert identity.path is None


def test_path_is_normalized() -> None:
    identity = LogicalSessionIdentity(
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        path="  ejtv  ",
        remote_ip="201.192.154.132",
    )

    assert identity.path == "ejtv"


def test_ipv6_is_normalized() -> None:
    identity = LogicalSessionIdentity(
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        path="ejtv",
        remote_ip="2001:0db8:0000:0000:0000:0000:0000:0001",
    )

    assert identity.remote_ip == "2001:db8::1"


def test_invalid_session_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="session must be an ActiveSession",
    ):
        LogicalSessionIdentity.from_session(
            "invalid"  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "value",
        "expected_exception",
        "expected_message",
    ),
    (
        (
            "protocol",
            "SRT",
            TypeError,
            "protocol must be a SessionProtocol",
        ),
        (
            "role",
            "READER",
            TypeError,
            "role must be a SessionRole",
        ),
        (
            "path",
            123,
            TypeError,
            "path must be a string or None",
        ),
        (
            "path",
            "   ",
            ValueError,
            "path must not be empty when provided",
        ),
        (
            "remote_ip",
            123,
            TypeError,
            "remote_ip must be a string",
        ),
        (
            "remote_ip",
            "   ",
            ValueError,
            "remote_ip must not be empty",
        ),
        (
            "remote_ip",
            "not-an-ip",
            ValueError,
            "remote_ip must contain a valid IP address",
        ),
    ),
)
def test_invalid_identity_values(
    field_name,
    value,
    expected_exception,
    expected_message,
) -> None:
    arguments = {
        "protocol": SessionProtocol.SRT,
        "role": SessionRole.READER,
        "path": "ejtv",
        "remote_ip": "201.192.154.132",
    }

    arguments[field_name] = value

    with pytest.raises(
        expected_exception,
        match=expected_message,
    ):
        LogicalSessionIdentity(
            **arguments,
        )
