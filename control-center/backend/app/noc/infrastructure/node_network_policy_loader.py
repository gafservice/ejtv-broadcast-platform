"""Load Node network-interface policy from YAML.

ENG-013B — Node SDK

This infrastructure component translates an external YAML
representation into canonical NOC domain objects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.noc.domain.network_interface_policy import (
    NetworkInterfacePolicy,
    NetworkInterfaceRole,
)
from app.noc.domain.node_network_policy_config import (
    NodeNetworkPolicyConfig,
)


class NodeNetworkPolicyLoader:
    """Load canonical Node network policy from YAML."""

    def load(
        self,
        path: str | Path,
    ) -> NodeNetworkPolicyConfig:
        """Load a network policy configuration from a YAML file."""

        config_path = self._normalize_path(path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Network policy file not found: {config_path}"
            )

        if not config_path.is_file():
            raise ValueError(
                f"Network policy path is not a file: {config_path}"
            )

        try:
            payload = yaml.safe_load(
                config_path.read_text(
                    encoding="utf-8"
                )
            )
        except yaml.YAMLError as exc:
            raise ValueError(
                "Invalid YAML network policy"
            ) from exc

        return self.from_mapping(payload)

    def from_mapping(
        self,
        payload: Any,
    ) -> NodeNetworkPolicyConfig:
        """Build canonical policy from decoded YAML data."""

        if payload is None:
            raise ValueError(
                "Network policy document must not be empty"
            )

        if not isinstance(payload, dict):
            raise TypeError(
                "Network policy root must be a mapping"
            )

        raw_interfaces = payload.get(
            "network_interfaces"
        )

        if raw_interfaces is None:
            raise ValueError(
                "network_interfaces is required"
            )

        if not isinstance(raw_interfaces, list):
            raise TypeError(
                "network_interfaces must be a list"
            )

        policies = tuple(
            self._build_policy(entry)
            for entry in raw_interfaces
        )

        return NodeNetworkPolicyConfig(
            interfaces=policies
        )

    @staticmethod
    def _build_policy(
        entry: Any,
    ) -> NetworkInterfacePolicy:
        """Translate one YAML entry into domain policy."""

        if not isinstance(entry, dict):
            raise TypeError(
                "network interface policy must be a mapping"
            )

        required_fields = (
            "interface",
            "role",
            "expected_up",
            "critical",
        )

        missing = tuple(
            field
            for field in required_fields
            if field not in entry
        )

        if missing:
            raise ValueError(
                "Missing network interface policy fields: "
                + ", ".join(missing)
            )

        return NetworkInterfacePolicy(
            interface=entry["interface"],
            role=NetworkInterfaceRole.from_value(
                entry["role"]
            ),
            expected_up=entry["expected_up"],
            critical=entry["critical"],
        )

    @staticmethod
    def _normalize_path(
        path: str | Path,
    ) -> Path:
        if isinstance(path, Path):
            return path

        if not isinstance(path, str):
            raise TypeError(
                "path must be a string or Path"
            )

        normalized = path.strip()

        if not normalized:
            raise ValueError(
                "path must not be empty"
            )

        return Path(normalized)
