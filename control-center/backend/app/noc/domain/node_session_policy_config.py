"""Node multimedia-session operational policy configuration.

ENG-013B — Node SDK

NodeSessionPolicyConfig groups the operational multimedia-session
policies configured for one NOC node.

It is an immutable domain configuration object. It does not load files,
capture sessions, evaluate runtime state or raise alarms.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)
from app.noc.domain.expected_session_policy import (
    ExpectedSessionPolicy,
)
from app.noc.domain.reconnect_flapping_policy import (
    ReconnectFlappingPolicy,
)


@dataclass(frozen=True, slots=True)
class NodeSessionPolicyConfig:
    """Operational multimedia-session policies for one node."""

    expected_sessions: tuple[
        ExpectedSessionPolicy,
        ...,
    ] = ()

    critical_paths: tuple[
        CriticalPathPolicy,
        ...,
    ] = ()

    reconnect_flapping: (
        ReconnectFlappingPolicy | None
    ) = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.expected_sessions,
            tuple,
        ):
            raise TypeError(
                "expected_sessions must be a tuple"
            )

        if not all(
            isinstance(
                policy,
                ExpectedSessionPolicy,
            )
            for policy in self.expected_sessions
        ):
            raise TypeError(
                "expected_sessions must contain only "
                "ExpectedSessionPolicy values"
            )

        if not isinstance(
            self.critical_paths,
            tuple,
        ):
            raise TypeError(
                "critical_paths must be a tuple"
            )

        if not all(
            isinstance(
                policy,
                CriticalPathPolicy,
            )
            for policy in self.critical_paths
        ):
            raise TypeError(
                "critical_paths must contain only "
                "CriticalPathPolicy values"
            )

        if (
            self.reconnect_flapping is not None
            and not isinstance(
                self.reconnect_flapping,
                ReconnectFlappingPolicy,
            )
        ):
            raise TypeError(
                "reconnect_flapping must be a "
                "ReconnectFlappingPolicy or None"
            )

        expected_ids = [
            policy.policy_id
            for policy in self.expected_sessions
        ]

        if len(expected_ids) != len(
            set(expected_ids)
        ):
            raise ValueError(
                "expected session policy identifiers "
                "must be unique"
            )

        critical_paths = [
            policy.path
            for policy in self.critical_paths
        ]

        if len(critical_paths) != len(
            set(critical_paths)
        ):
            raise ValueError(
                "critical path policy paths "
                "must be unique"
            )

    def __len__(self) -> int:
        """Return the total number of configured session policies."""

        return (
            len(self.expected_sessions)
            + len(self.critical_paths)
            + (
                1
                if self.reconnect_flapping
                is not None
                else 0
            )
        )

    @property
    def has_expected_sessions(self) -> bool:
        """Return whether expected-session policies exist."""

        return bool(self.expected_sessions)

    @property
    def has_critical_paths(self) -> bool:
        """Return whether critical-path policies exist."""

        return bool(self.critical_paths)

    @property
    def has_reconnect_flapping(self) -> bool:
        """Return whether reconnect-flapping detection is configured."""

        return self.reconnect_flapping is not None
