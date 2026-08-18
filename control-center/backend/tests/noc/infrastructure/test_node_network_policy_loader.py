"""Tests for NodeNetworkPolicyLoader."""

from pathlib import Path

import pytest

from app.noc.domain.network_interface_policy import (
    NetworkInterfaceRole,
)
from app.noc.infrastructure.node_network_policy_loader import (
    NodeNetworkPolicyLoader,
)


def test_loads_valid_yaml(
    tmp_path: Path,
) -> None:
    path = tmp_path / "node.yaml"

    path.write_text(
        """
node: node-01

network_interfaces:
  - interface: enp9s0
    role: INGEST
    expected_up: true
    critical: true

  - interface: ens2f1
    role: BACKUP
    expected_up: false
    critical: false
""".strip(),
        encoding="utf-8",
    )

    config = NodeNetworkPolicyLoader().load(path)

    assert len(config) == 2

    ingest = config.get("enp9s0")

    assert ingest is not None
    assert ingest.role is NetworkInterfaceRole.INGEST
    assert ingest.expected_up is True
    assert ingest.critical is True

    backup = config.get("ens2f1")

    assert backup is not None
    assert backup.role is NetworkInterfaceRole.BACKUP
    assert backup.expected_up is False


def test_real_ejtv_profile_can_be_loaded() -> None:
    path = Path(
        "../config/nodes/ejtv-01.yaml"
    )

    config = NodeNetworkPolicyLoader().load(path)

    assert len(config) == 5

    assert config.get("enp9s0") is not None
    assert config.get("ens2f0") is not None
    assert config.get("ens2f1") is not None
    assert config.get("enp10s0") is not None
    assert config.get("lo") is not None


def test_empty_document_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError):
        NodeNetworkPolicyLoader().load(path)


def test_missing_network_interfaces_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid.yaml"

    path.write_text(
        "node: node-01\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        NodeNetworkPolicyLoader().load(path)


def test_network_interfaces_must_be_list() -> None:
    with pytest.raises(TypeError):
        NodeNetworkPolicyLoader().from_mapping(
            {
                "network_interfaces": {},
            }
        )


def test_missing_policy_field_is_rejected() -> None:
    with pytest.raises(ValueError):
        NodeNetworkPolicyLoader().from_mapping(
            {
                "network_interfaces": [
                    {
                        "interface": "enp9s0",
                        "role": "INGEST",
                    }
                ]
            }
        )


def test_invalid_role_is_rejected() -> None:
    with pytest.raises(ValueError):
        NodeNetworkPolicyLoader().from_mapping(
            {
                "network_interfaces": [
                    {
                        "interface": "enp9s0",
                        "role": "INVALID",
                        "expected_up": True,
                        "critical": True,
                    }
                ]
            }
        )


def test_duplicate_interfaces_are_rejected() -> None:
    with pytest.raises(ValueError):
        NodeNetworkPolicyLoader().from_mapping(
            {
                "network_interfaces": [
                    {
                        "interface": "ens2f0",
                        "role": "PUBLICATION",
                        "expected_up": True,
                        "critical": True,
                    },
                    {
                        "interface": "ens2f0",
                        "role": "BACKUP",
                        "expected_up": False,
                        "critical": False,
                    },
                ]
            }
        )


def test_missing_file_is_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError):
        NodeNetworkPolicyLoader().load(
            tmp_path / "missing.yaml"
        )


def test_path_must_be_valid_type() -> None:
    with pytest.raises(TypeError):
        NodeNetworkPolicyLoader().load(
            123  # type: ignore[arg-type]
        )
