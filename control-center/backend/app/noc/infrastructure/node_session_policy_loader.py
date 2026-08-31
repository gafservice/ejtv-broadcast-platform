"""YAML loader for node multimedia-session operational policies.

ENG-013B — Node SDK

NodeSessionPolicyLoader reads the session_policies section of one node
configuration document and converts it into immutable domain policies.

The loader deliberately ignores unrelated sections such as
network_interfaces.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any, Mapping

import yaml

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


class NodeSessionPolicyLoader:
    """Load multimedia-session policies from node YAML configuration."""

    def load(
        self,
        path: str | Path,
    ) -> NodeSessionPolicyConfig:
        """Load policies from a YAML document."""

        if not isinstance(path, (str, Path)):
            raise TypeError(
                "path must be a string or Path"
            )

        resolved = Path(path)

        if not resolved.exists():
            raise FileNotFoundError(resolved)

        raw = yaml.safe_load(
            resolved.read_text(
                encoding="utf-8"
            )
        )

        if raw is None:
            raise ValueError(
                "node policy document must not be empty"
            )

        if not isinstance(raw, Mapping):
            raise TypeError(
                "node policy document must be a mapping"
            )

        return self.from_mapping(raw)

    def from_mapping(
        self,
        data: Mapping[str, Any],
    ) -> NodeSessionPolicyConfig:
        """Build session policies from a parsed node mapping."""

        if not isinstance(data, Mapping):
            raise TypeError(
                "data must be a mapping"
            )

        raw_session_policies = data.get(
            "session_policies"
        )

        if raw_session_policies is None:
            return NodeSessionPolicyConfig()

        if not isinstance(
            raw_session_policies,
            Mapping,
        ):
            raise TypeError(
                "session_policies must be a mapping"
            )

        expected_sessions = (
            self._load_expected_sessions(
                raw_session_policies.get(
                    "expected_sessions",
                    [],
                )
            )
        )

        critical_paths = (
            self._load_critical_paths(
                raw_session_policies.get(
                    "critical_paths",
                    [],
                )
            )
        )

        reconnect_flapping = (
            self._load_reconnect_flapping(
                raw_session_policies.get(
                    "reconnect_flapping"
                )
            )
        )

        return NodeSessionPolicyConfig(
            expected_sessions=expected_sessions,
            critical_paths=critical_paths,
            reconnect_flapping=reconnect_flapping,
        )

    def _load_expected_sessions(
        self,
        value: Any,
    ) -> tuple[ExpectedSessionPolicy, ...]:
        if not isinstance(value, list):
            raise TypeError(
                "expected_sessions must be a list"
            )

        policies: list[
            ExpectedSessionPolicy
        ] = []

        for item in value:
            if not isinstance(item, Mapping):
                raise TypeError(
                    "expected session entries must be mappings"
                )

            try:
                policy_id = item["policy_id"]
                protocol_raw = item["protocol"]
                role_raw = item["role"]
                path = item.get("path")
            except KeyError as exc:
                raise ValueError(
                    f"missing expected session field: {exc.args[0]}"
                ) from exc

            enabled = item.get(
                "enabled",
                True,
            )

            missing_grace_seconds = item.get(
                "missing_grace_seconds",
                15,
            )

            self._validate_seconds(
                missing_grace_seconds,
                field_name="missing_grace_seconds",
                allow_zero=True,
            )

            policies.append(
                ExpectedSessionPolicy(
                    policy_id=policy_id,
                    protocol=self._parse_protocol(
                        protocol_raw
                    ),
                    role=self._parse_role(
                        role_raw
                    ),
                    path=path,
                    enabled=enabled,
                    missing_grace_period=timedelta(
                        seconds=missing_grace_seconds
                    ),
                )
            )

        return tuple(policies)

    def _load_critical_paths(
        self,
        value: Any,
    ) -> tuple[CriticalPathPolicy, ...]:
        if not isinstance(value, list):
            raise TypeError(
                "critical_paths must be a list"
            )

        policies: list[
            CriticalPathPolicy
        ] = []

        for item in value:
            if not isinstance(item, Mapping):
                raise TypeError(
                    "critical path entries must be mappings"
                )

            if "path" not in item:
                raise ValueError(
                    "missing critical path field: path"
                )

            enabled = item.get(
                "enabled",
                True,
            )

            grace_seconds = item.get(
                "no_readers_grace_seconds",
                15,
            )

            unavailable_grace_seconds = item.get(
                "unavailable_grace_seconds",
                15,
            )

            traffic_stalled_grace_seconds = item.get(
                "traffic_stalled_grace_seconds",
                15,
            )

            self._validate_seconds(
                grace_seconds,
                field_name=(
                    "no_readers_grace_seconds"
                ),
                allow_zero=True,
            )

            self._validate_seconds(
                unavailable_grace_seconds,
                field_name=(
                    "unavailable_grace_seconds"
                ),
                allow_zero=True,
            )

            self._validate_seconds(
                traffic_stalled_grace_seconds,
                field_name=(
                    "traffic_stalled_grace_seconds"
                ),
                allow_zero=True,
            )

            policies.append(
                CriticalPathPolicy(
                    path=item["path"],
                    enabled=enabled,
                    no_readers_grace_period=timedelta(
                        seconds=grace_seconds
                    ),
                    unavailable_grace_period=timedelta(
                        seconds=unavailable_grace_seconds
                    ),
                    traffic_stalled_grace_period=timedelta(
                        seconds=traffic_stalled_grace_seconds
                    ),
                )
            )

        return tuple(policies)

    def _load_reconnect_flapping(
        self,
        value: Any,
    ) -> ReconnectFlappingPolicy | None:
        if value is None:
            return None

        if not isinstance(value, Mapping):
            raise TypeError(
                "reconnect_flapping must be a mapping"
            )

        reconnect_timeout_seconds = value.get(
            "reconnect_timeout_seconds",
            10,
        )

        window_seconds = value.get(
            "window_seconds",
            60,
        )

        threshold = value.get(
            "threshold",
            3,
        )

        self._validate_seconds(
            reconnect_timeout_seconds,
            field_name=(
                "reconnect_timeout_seconds"
            ),
            allow_zero=False,
        )

        self._validate_seconds(
            window_seconds,
            field_name="window_seconds",
            allow_zero=False,
        )

        return ReconnectFlappingPolicy(
            reconnect_timeout=timedelta(
                seconds=reconnect_timeout_seconds
            ),
            window=timedelta(
                seconds=window_seconds
            ),
            threshold=threshold,
        )

    @staticmethod
    def _parse_protocol(
        value: Any,
    ) -> SessionProtocol:
        if not isinstance(value, str):
            raise TypeError(
                "protocol must be a string"
            )

        normalized = value.strip().upper()

        try:
            return SessionProtocol(
                normalized
            )
        except ValueError as exc:
            raise ValueError(
                f"unsupported session protocol: {value}"
            ) from exc

    @staticmethod
    def _parse_role(
        value: Any,
    ) -> SessionRole:
        if not isinstance(value, str):
            raise TypeError(
                "role must be a string"
            )

        normalized = value.strip().upper()

        try:
            return SessionRole(
                normalized
            )
        except ValueError as exc:
            raise ValueError(
                f"unsupported session role: {value}"
            ) from exc

    @staticmethod
    def _validate_seconds(
        value: Any,
        *,
        field_name: str,
        allow_zero: bool,
    ) -> None:
        if not isinstance(value, int):
            raise TypeError(
                f"{field_name} must be an int"
            )

        if isinstance(value, bool):
            raise TypeError(
                f"{field_name} must be an int"
            )

        if allow_zero:
            if value < 0:
                raise ValueError(
                    f"{field_name} must not be negative"
                )
        elif value <= 0:
            raise ValueError(
                f"{field_name} must be greater than zero"
            )
