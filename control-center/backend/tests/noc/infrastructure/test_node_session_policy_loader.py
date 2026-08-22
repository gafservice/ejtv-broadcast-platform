"""Tests for NodeSessionPolicyLoader."""

from datetime import timedelta
from pathlib import Path

import pytest

from app.domain.sessions import (
    SessionProtocol,
    SessionRole,
)
from app.noc.infrastructure.node_session_policy_loader import (
    NodeSessionPolicyLoader,
)


def test_missing_session_policies_returns_empty_config() -> None:
    config = NodeSessionPolicyLoader().from_mapping(
        {
            "node": "node-01",
            "network_interfaces": [],
        }
    )

    assert len(config) == 0
    assert config.expected_sessions == ()
    assert config.critical_paths == ()
    assert config.reconnect_flapping is None


def test_loads_complete_session_policy_mapping() -> None:
    config = NodeSessionPolicyLoader().from_mapping(
        {
            "session_policies": {
                "expected_sessions": [
                    {
                        "policy_id": "ejtv-publication",
                        "protocol": "SRT",
                        "role": "PUBLISHER",
                        "path": "ejtv",
                        "enabled": True,
                        "missing_grace_seconds": 20,
                    },
                    {
                        "policy_id": "ejtv-reader",
                        "protocol": "rtsp",
                        "role": "reader",
                        "path": "ejtv",
                    },
                ],
                "critical_paths": [
                    {
                        "path": "ejtv",
                        "enabled": True,
                        "no_readers_grace_seconds": 30,
                    }
                ],
                "reconnect_flapping": {
                    "reconnect_timeout_seconds": 5,
                    "window_seconds": 120,
                    "threshold": 4,
                },
            }
        }
    )

    assert len(config.expected_sessions) == 2

    first = config.expected_sessions[0]

    assert first.policy_id == "ejtv-publication"
    assert first.protocol is SessionProtocol.SRT
    assert first.role is SessionRole.PUBLISHER
    assert first.path == "ejtv"
    assert (
        first.missing_grace_period
        == timedelta(seconds=20)
    )

    second = config.expected_sessions[1]

    assert second.protocol is SessionProtocol.RTSP
    assert second.role is SessionRole.READER

    assert len(config.critical_paths) == 1

    critical = config.critical_paths[0]

    assert critical.path == "ejtv"
    assert (
        critical.no_readers_grace_period
        == timedelta(seconds=30)
    )

    assert config.reconnect_flapping is not None

    assert (
        config.reconnect_flapping.reconnect_timeout
        == timedelta(seconds=5)
    )

    assert (
        config.reconnect_flapping.window
        == timedelta(seconds=120)
    )

    assert (
        config.reconnect_flapping.threshold
        == 4
    )


def test_defaults_are_applied() -> None:
    config = NodeSessionPolicyLoader().from_mapping(
        {
            "session_policies": {
                "expected_sessions": [
                    {
                        "policy_id": "expected",
                        "protocol": "SRT",
                        "role": "READER",
                        "path": "ejtv",
                    }
                ],
                "critical_paths": [
                    {
                        "path": "ejtv",
                    }
                ],
                "reconnect_flapping": {},
            }
        }
    )

    expected = config.expected_sessions[0]

    assert expected.enabled is True
    assert (
        expected.missing_grace_period
        == timedelta(seconds=15)
    )

    critical = config.critical_paths[0]

    assert critical.enabled is True
    assert (
        critical.no_readers_grace_period
        == timedelta(seconds=15)
    )

    assert config.reconnect_flapping is not None

    assert (
        config.reconnect_flapping.reconnect_timeout
        == timedelta(seconds=10)
    )
    assert (
        config.reconnect_flapping.window
        == timedelta(seconds=60)
    )
    assert config.reconnect_flapping.threshold == 3


def test_loads_yaml_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "node.yaml"

    path.write_text(
        """
node: node-01

network_interfaces: []

session_policies:
  expected_sessions:
    - policy_id: ingest-reader
      protocol: SRT
      role: READER
      path: ingest
      missing_grace_seconds: 10

  critical_paths:
    - path: ingest
      no_readers_grace_seconds: 20

  reconnect_flapping:
    reconnect_timeout_seconds: 5
    window_seconds: 30
    threshold: 2
""".strip(),
        encoding="utf-8",
    )

    config = NodeSessionPolicyLoader().load(
        path
    )

    assert len(config) == 3


def test_empty_document_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "empty.yaml"

    path.write_text(
        "",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        NodeSessionPolicyLoader().load(
            path
        )


def test_session_policies_must_be_mapping() -> None:
    with pytest.raises(TypeError):
        NodeSessionPolicyLoader().from_mapping(
            {
                "session_policies": [],
            }
        )


def test_expected_sessions_must_be_list() -> None:
    with pytest.raises(TypeError):
        NodeSessionPolicyLoader().from_mapping(
            {
                "session_policies": {
                    "expected_sessions": {},
                }
            }
        )


def test_critical_paths_must_be_list() -> None:
    with pytest.raises(TypeError):
        NodeSessionPolicyLoader().from_mapping(
            {
                "session_policies": {
                    "critical_paths": {},
                }
            }
        )


def test_reconnect_flapping_must_be_mapping() -> None:
    with pytest.raises(TypeError):
        NodeSessionPolicyLoader().from_mapping(
            {
                "session_policies": {
                    "reconnect_flapping": [],
                }
            }
        )


def test_invalid_protocol_is_rejected() -> None:
    with pytest.raises(ValueError):
        NodeSessionPolicyLoader().from_mapping(
            {
                "session_policies": {
                    "expected_sessions": [
                        {
                            "policy_id": "bad",
                            "protocol": "INVALID",
                            "role": "READER",
                            "path": "ejtv",
                        }
                    ]
                }
            }
        )


def test_invalid_role_is_rejected() -> None:
    with pytest.raises(ValueError):
        NodeSessionPolicyLoader().from_mapping(
            {
                "session_policies": {
                    "expected_sessions": [
                        {
                            "policy_id": "bad",
                            "protocol": "SRT",
                            "role": "INVALID",
                            "path": "ejtv",
                        }
                    ]
                }
            }
        )


def test_duplicate_policy_ids_are_rejected() -> None:
    with pytest.raises(ValueError):
        NodeSessionPolicyLoader().from_mapping(
            {
                "session_policies": {
                    "expected_sessions": [
                        {
                            "policy_id": "duplicate",
                            "protocol": "SRT",
                            "role": "READER",
                            "path": "ejtv",
                        },
                        {
                            "policy_id": "duplicate",
                            "protocol": "RTSP",
                            "role": "READER",
                            "path": "ejtv",
                        },
                    ]
                }
            }
        )


def test_duplicate_critical_paths_are_rejected() -> None:
    with pytest.raises(ValueError):
        NodeSessionPolicyLoader().from_mapping(
            {
                "session_policies": {
                    "critical_paths": [
                        {
                            "path": "ejtv",
                        },
                        {
                            "path": "ejtv",
                        },
                    ]
                }
            }
        )


def test_missing_file_is_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError):
        NodeSessionPolicyLoader().load(
            tmp_path / "missing.yaml"
        )


def test_path_must_be_valid_type() -> None:
    with pytest.raises(TypeError):
        NodeSessionPolicyLoader().load(
            123  # type: ignore[arg-type]
        )


def test_real_ejtv_profile_can_be_loaded() -> None:
    path = Path(
        "../config/nodes/ejtv-01.yaml"
    )

    config = NodeSessionPolicyLoader().load(
        path
    )

    assert len(config.expected_sessions) == 1

    expected = config.expected_sessions[0]

    assert expected.policy_id == "ejtv-publication"
    assert expected.protocol is SessionProtocol.SRT
    assert expected.role is SessionRole.PUBLISHER
    assert expected.path == "ejtv"
    assert (
        expected.missing_grace_period
        == timedelta(seconds=15)
    )

    assert len(config.critical_paths) == 1

    critical = config.critical_paths[0]

    assert critical.path == "ejtv"
    assert (
        critical.no_readers_grace_period
        == timedelta(seconds=15)
    )

    assert config.reconnect_flapping is not None

    assert (
        config.reconnect_flapping.reconnect_timeout
        == timedelta(seconds=10)
    )

    assert (
        config.reconnect_flapping.window
        == timedelta(seconds=60)
    )

    assert config.reconnect_flapping.threshold == 3
