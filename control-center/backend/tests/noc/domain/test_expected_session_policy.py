from datetime import UTC, datetime, timedelta

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.expected_session_policy import (
    ExpectedSessionPolicy,
)


TIMESTAMP = datetime(
    2026,
    8,
    22,
    23,
    30,
    tzinfo=UTC,
)


def build_session(
    *,
    protocol: SessionProtocol = SessionProtocol.SRT,
    role: SessionRole = SessionRole.READER,
    path: str | None = "ejtv",
) -> ActiveSession:
    return ActiveSession(
        session_id="session-001",
        protocol=protocol,
        role=role,
        state="read",
        remote_ip="201.192.154.132",
        remote_port=50000,
        path=path,
        connected_since=TIMESTAMP,
    )


def build_policy(
    *,
    policy_id: str = "ejtv-srt-reader",
    protocol: SessionProtocol = SessionProtocol.SRT,
    role: SessionRole = SessionRole.READER,
    path: str | None = "ejtv",
    enabled: bool = True,
) -> ExpectedSessionPolicy:
    return ExpectedSessionPolicy(
        policy_id=policy_id,
        protocol=protocol,
        role=role,
        path=path,
        enabled=enabled,
    )


def test_policy_normalizes_policy_id() -> None:
    policy = build_policy(
        policy_id="  ejtv-srt-reader  "
    )

    assert policy.policy_id == "ejtv-srt-reader"


def test_policy_normalizes_path() -> None:
    policy = build_policy(
        path="  ejtv  "
    )

    assert policy.path == "ejtv"


def test_policy_supports_none_path() -> None:
    policy = build_policy(
        path=None
    )

    assert policy.path is None


def test_policy_defaults_to_enabled() -> None:
    policy = build_policy()

    assert policy.enabled is True


def test_matches_expected_session() -> None:
    policy = build_policy()

    assert policy.matches(
        build_session()
    ) is True


def test_different_protocol_does_not_match() -> None:
    policy = build_policy(
        protocol=SessionProtocol.SRT,
    )

    session = build_session(
        protocol=SessionProtocol.RTSP,
    )

    assert policy.matches(session) is False


def test_different_role_does_not_match() -> None:
    policy = build_policy(
        role=SessionRole.READER,
    )

    session = build_session(
        role=SessionRole.PUBLISHER,
    )

    assert policy.matches(session) is False


def test_different_path_does_not_match() -> None:
    policy = build_policy(
        path="ejtv",
    )

    session = build_session(
        path="enlace",
    )

    assert policy.matches(session) is False


def test_none_path_matches_none_path() -> None:
    policy = build_policy(
        path=None,
    )

    session = build_session(
        path=None,
    )

    assert policy.matches(session) is True


def test_matches_rejects_invalid_session() -> None:
    policy = build_policy()

    with pytest.raises(
        TypeError,
        match="session must be an ActiveSession",
    ):
        policy.matches(
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
            "policy_id",
            123,
            TypeError,
            "policy_id must be a string",
        ),
        (
            "policy_id",
            "   ",
            ValueError,
            "policy_id must not be empty",
        ),
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
            "enabled",
            "yes",
            TypeError,
            "enabled must be a bool",
        ),
    ),
)
def test_policy_rejects_invalid_values(
    field_name,
    value,
    expected_exception,
    expected_message,
) -> None:
    arguments = {
        "policy_id": "ejtv-srt-reader",
        "protocol": SessionProtocol.SRT,
        "role": SessionRole.READER,
        "path": "ejtv",
        "enabled": True,
    }

    arguments[field_name] = value

    with pytest.raises(
        expected_exception,
        match=expected_message,
    ):
        ExpectedSessionPolicy(
            **arguments,
        )


def test_default_missing_grace_period() -> None:
    policy = build_policy()

    assert (
        policy.missing_grace_period
        == timedelta(seconds=15)
    )


def test_custom_missing_grace_period() -> None:
    policy = ExpectedSessionPolicy(
        policy_id="ejtv-srt-reader",
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        path="ejtv",
        missing_grace_period=timedelta(seconds=30),
    )

    assert (
        policy.missing_grace_period
        == timedelta(seconds=30)
    )


def test_missing_grace_period_may_be_zero() -> None:
    policy = ExpectedSessionPolicy(
        policy_id="ejtv-srt-reader",
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        path="ejtv",
        missing_grace_period=timedelta(0),
    )

    assert policy.missing_grace_period == timedelta(0)


def test_invalid_missing_grace_period_type() -> None:
    with pytest.raises(
        TypeError,
        match="missing_grace_period must be a timedelta",
    ):
        ExpectedSessionPolicy(
            policy_id="ejtv-srt-reader",
            protocol=SessionProtocol.SRT,
            role=SessionRole.READER,
            path="ejtv",
            missing_grace_period=15,  # type: ignore[arg-type]
        )


def test_negative_missing_grace_period() -> None:
    with pytest.raises(
        ValueError,
        match="missing_grace_period must not be negative",
    ):
        ExpectedSessionPolicy(
            policy_id="ejtv-srt-reader",
            protocol=SessionProtocol.SRT,
            role=SessionRole.READER,
            path="ejtv",
            missing_grace_period=timedelta(seconds=-1),
        )
