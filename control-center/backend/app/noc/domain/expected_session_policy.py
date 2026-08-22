"""Expected multimedia session policy for the NOC.

ENG-013B — Node SDK

ExpectedSessionPolicy describes a multimedia session that is expected to
be observable on a node instance.

The policy represents operational intent, not a concrete transport
connection. Therefore it deliberately does not use session_id as its
identity.

A concrete ActiveSession satisfies the policy when protocol, role and
path match.

This module does not capture sessions, maintain history, raise alarms or
perform temporal stabilization.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
)


@dataclass(frozen=True, slots=True)
class ExpectedSessionPolicy:
    """Operational expectation for one multimedia session."""

    policy_id: str
    protocol: SessionProtocol
    role: SessionRole
    path: str | None
    enabled: bool = True
    missing_grace_period: timedelta = timedelta(seconds=15)

    def __post_init__(self) -> None:
        if not isinstance(self.policy_id, str):
            raise TypeError(
                "policy_id must be a string"
            )

        normalized_policy_id = self.policy_id.strip()

        if not normalized_policy_id:
            raise ValueError(
                "policy_id must not be empty"
            )

        object.__setattr__(
            self,
            "policy_id",
            normalized_policy_id,
        )

        if not isinstance(
            self.protocol,
            SessionProtocol,
        ):
            raise TypeError(
                "protocol must be a SessionProtocol"
            )

        if not isinstance(
            self.role,
            SessionRole,
        ):
            raise TypeError(
                "role must be a SessionRole"
            )

        if self.path is not None:
            if not isinstance(self.path, str):
                raise TypeError(
                    "path must be a string or None"
                )

            normalized_path = self.path.strip()

            if not normalized_path:
                raise ValueError(
                    "path must not be empty when provided"
                )

            object.__setattr__(
                self,
                "path",
                normalized_path,
            )

        if not isinstance(self.enabled, bool):
            raise TypeError(
                "enabled must be a bool"
            )

        if not isinstance(
            self.missing_grace_period,
            timedelta,
        ):
            raise TypeError(
                "missing_grace_period must be a timedelta"
            )

        if self.missing_grace_period < timedelta(0):
            raise ValueError(
                "missing_grace_period must not be negative"
            )

    def matches(
        self,
        session: ActiveSession,
    ) -> bool:
        """Return whether a concrete session satisfies this policy."""

        if not isinstance(session, ActiveSession):
            raise TypeError(
                "session must be an ActiveSession"
            )

        return (
            session.protocol is self.protocol
            and session.role is self.role
            and session.path == self.path
        )
