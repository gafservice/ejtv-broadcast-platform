"""Tests for NodeSessionPolicyConfig."""

from datetime import timedelta

import pytest

from app.domain.sessions import (
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)
from app.noc.domain.expected_session_policy import (
    ExpectedSessionPolicy,
)
from app.noc.domain.node_session_policy_config import (
    NodeSessionPolicyConfig,
)
from app.noc.domain.reconnect_flapping_policy import (
    ReconnectFlappingPolicy,
)


def make_expected_policy(
    *,
    policy_id: str = "ejtv-publication",
    path: str = "ejtv",
) -> ExpectedSessionPolicy:
    return ExpectedSessionPolicy(
        policy_id=policy_id,
        protocol=SessionProtocol.SRT,
        role=SessionRole.PUBLISHER,
        path=path,
        missing_grace_period=timedelta(
            seconds=15
        ),
    )


def make_critical_path(
    *,
    path: str = "ejtv",
) -> CriticalPathPolicy:
    return CriticalPathPolicy(
        path=path,
        no_readers_grace_period=timedelta(
            seconds=15
        ),
    )


def make_flapping_policy() -> ReconnectFlappingPolicy:
    return ReconnectFlappingPolicy(
        reconnect_timeout=timedelta(
            seconds=10
        ),
        window=timedelta(
            seconds=60
        ),
        threshold=3,
    )


def test_empty_config() -> None:
    config = NodeSessionPolicyConfig()

    assert config.expected_sessions == ()
    assert config.critical_paths == ()
    assert config.reconnect_flapping is None
    assert len(config) == 0

    assert config.has_expected_sessions is False
    assert config.has_critical_paths is False
    assert config.has_reconnect_flapping is False


def test_complete_config() -> None:
    expected = make_expected_policy()
    critical = make_critical_path()
    flapping = make_flapping_policy()

    config = NodeSessionPolicyConfig(
        expected_sessions=(expected,),
        critical_paths=(critical,),
        reconnect_flapping=flapping,
    )

    assert config.expected_sessions == (
        expected,
    )

    assert config.critical_paths == (
        critical,
    )

    assert config.reconnect_flapping is flapping

    assert len(config) == 3

    assert config.has_expected_sessions is True
    assert config.has_critical_paths is True
    assert config.has_reconnect_flapping is True


def test_multiple_expected_sessions() -> None:
    first = make_expected_policy(
        policy_id="ejtv-publication",
    )

    second = ExpectedSessionPolicy(
        policy_id="ejtv-reader",
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        path="ejtv",
    )

    config = NodeSessionPolicyConfig(
        expected_sessions=(
            first,
            second,
        )
    )

    assert len(config.expected_sessions) == 2
    assert len(config) == 2


def test_multiple_critical_paths() -> None:
    first = make_critical_path(
        path="ejtv",
    )

    second = make_critical_path(
        path="enlace",
    )

    config = NodeSessionPolicyConfig(
        critical_paths=(
            first,
            second,
        )
    )

    assert len(config.critical_paths) == 2
    assert len(config) == 2


def test_rejects_non_tuple_expected_sessions() -> None:
    with pytest.raises(TypeError):
        NodeSessionPolicyConfig(
            expected_sessions=[
                make_expected_policy()
            ],  # type: ignore[arg-type]
        )


def test_rejects_invalid_expected_session_entry() -> None:
    with pytest.raises(TypeError):
        NodeSessionPolicyConfig(
            expected_sessions=(
                object(),  # type: ignore[arg-type]
            )
        )


def test_rejects_non_tuple_critical_paths() -> None:
    with pytest.raises(TypeError):
        NodeSessionPolicyConfig(
            critical_paths=[
                make_critical_path()
            ],  # type: ignore[arg-type]
        )


def test_rejects_invalid_critical_path_entry() -> None:
    with pytest.raises(TypeError):
        NodeSessionPolicyConfig(
            critical_paths=(
                object(),  # type: ignore[arg-type]
            )
        )


def test_rejects_invalid_reconnect_flapping() -> None:
    with pytest.raises(TypeError):
        NodeSessionPolicyConfig(
            reconnect_flapping=(
                object()  # type: ignore[arg-type]
            )
        )


def test_rejects_duplicate_expected_policy_ids() -> None:
    first = make_expected_policy(
        policy_id="ejtv-publication",
    )

    second = ExpectedSessionPolicy(
        policy_id="ejtv-publication",
        protocol=SessionProtocol.RTMP,
        role=SessionRole.PUBLISHER,
        path="ejtv",
    )

    with pytest.raises(ValueError):
        NodeSessionPolicyConfig(
            expected_sessions=(
                first,
                second,
            )
        )


def test_rejects_duplicate_critical_paths() -> None:
    first = make_critical_path(
        path="ejtv",
    )

    second = CriticalPathPolicy(
        path="ejtv",
        no_readers_grace_period=timedelta(
            seconds=30
        ),
    )

    with pytest.raises(ValueError):
        NodeSessionPolicyConfig(
            critical_paths=(
                first,
                second,
            )
        )


def test_len_counts_all_policy_types() -> None:
    config = NodeSessionPolicyConfig(
        expected_sessions=(
            make_expected_policy(
                policy_id="publication",
            ),
            ExpectedSessionPolicy(
                policy_id="reader",
                protocol=SessionProtocol.SRT,
                role=SessionRole.READER,
                path="ejtv",
            ),
        ),
        critical_paths=(
            make_critical_path(
                path="ejtv",
            ),
            make_critical_path(
                path="enlace",
            ),
        ),
        reconnect_flapping=(
            make_flapping_policy()
        ),
    )

    assert len(config) == 5
