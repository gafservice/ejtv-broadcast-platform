"""Logical multimedia session identity for the NOC.

ENG-013B — Node SDK

LogicalSessionIdentity identifies an operational multimedia relationship
across concrete transport reconnections.

It deliberately excludes session_id and remote_port because both may
change when the same logical client reconnects.

The initial identity contract is:

    protocol + role + path + remote_ip

This model does not detect transitions, maintain reconnect history or
raise alarms.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
)


@dataclass(frozen=True, slots=True)
class LogicalSessionIdentity:
    """Stable operational identity across concrete reconnections."""

    protocol: SessionProtocol
    role: SessionRole
    path: str | None
    remote_ip: str

    def __post_init__(self) -> None:
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

        if not isinstance(self.remote_ip, str):
            raise TypeError(
                "remote_ip must be a string"
            )

        normalized_remote_ip = self.remote_ip.strip()

        if not normalized_remote_ip:
            raise ValueError(
                "remote_ip must not be empty"
            )

        try:
            normalized_remote_ip = str(
                ip_address(normalized_remote_ip)
            )
        except ValueError as exc:
            raise ValueError(
                "remote_ip must contain a valid IP address"
            ) from exc

        object.__setattr__(
            self,
            "remote_ip",
            normalized_remote_ip,
        )

    @classmethod
    def from_session(
        cls,
        session: ActiveSession,
    ) -> "LogicalSessionIdentity":
        """Build logical identity from one concrete session."""

        if not isinstance(session, ActiveSession):
            raise TypeError(
                "session must be an ActiveSession"
            )

        return cls(
            protocol=session.protocol,
            role=session.role,
            path=session.path,
            remote_ip=session.remote_ip,
        )
