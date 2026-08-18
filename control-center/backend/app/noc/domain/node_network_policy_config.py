"""Network policy configuration for a NOC Node.

ENG-013B — Node SDK

Represents the complete declarative network-interface policy assigned
to one logical Node.

This model is independent from the configuration file format. YAML,
JSON, TOML or another external representation may later be translated
into this canonical domain object.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.noc.domain.network_interface_policy import (
    NetworkInterfacePolicy,
)


@dataclass(frozen=True, slots=True)
class NodeNetworkPolicyConfig:
    """Complete network-interface policy for one Node."""

    interfaces: tuple[NetworkInterfacePolicy, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.interfaces, tuple):
            raise TypeError(
                "interfaces must be a tuple"
            )

        seen: set[str] = set()

        for policy in self.interfaces:
            if not isinstance(
                policy,
                NetworkInterfacePolicy,
            ):
                raise TypeError(
                    "interfaces must contain "
                    "NetworkInterfacePolicy objects"
                )

            if policy.interface in seen:
                raise ValueError(
                    "duplicate network interface policy: "
                    f"{policy.interface}"
                )

            seen.add(policy.interface)

    def get(
        self,
        interface: str,
    ) -> NetworkInterfacePolicy | None:
        """Return policy for one interface."""

        if not isinstance(interface, str):
            raise TypeError(
                "interface must be a string"
            )

        normalized = interface.strip()

        if not normalized:
            raise ValueError(
                "interface must not be empty"
            )

        for policy in self.interfaces:
            if policy.interface == normalized:
                return policy

        return None

    def requires(
        self,
        interface: str,
    ) -> bool:
        """Return whether the interface has declared policy."""

        return self.get(interface) is not None

    @property
    def required_interfaces(
        self,
    ) -> tuple[NetworkInterfacePolicy, ...]:
        """Return interfaces expected to be operational."""

        return tuple(
            policy
            for policy in self.interfaces
            if policy.expected_up
        )

    @property
    def optional_interfaces(
        self,
    ) -> tuple[NetworkInterfacePolicy, ...]:
        """Return interfaces allowed to remain down."""

        return tuple(
            policy
            for policy in self.interfaces
            if not policy.expected_up
        )

    @property
    def critical_interfaces(
        self,
    ) -> tuple[NetworkInterfacePolicy, ...]:
        """Return interfaces declared operationally critical."""

        return tuple(
            policy
            for policy in self.interfaces
            if policy.critical
        )

    def __len__(self) -> int:
        return len(self.interfaces)

    def __contains__(self, interface: object) -> bool:
        if not isinstance(interface, str):
            return False

        normalized = interface.strip()

        if not normalized:
            return False

        return any(
            policy.interface == normalized
            for policy in self.interfaces
        )
