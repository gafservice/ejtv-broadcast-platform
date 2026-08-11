"""Functional capabilities exposed by a NodeInstance.

ENG-013B — Node SDK
NCS reference: 14-NODE-CAPABILITY.md
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CapabilityCategory(str, Enum):
    """Canonical capability categories defined by NCS v1.0.0."""

    PROTOCOL = "PROTOCOL"
    SECURITY = "SECURITY"
    PROCESSING = "PROCESSING"
    STORAGE = "STORAGE"
    MONITORING = "MONITORING"
    AUTOMATION = "AUTOMATION"
    OTHER = "OTHER"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(cls, value: str) -> "CapabilityCategory":
        if not isinstance(value, str):
            raise TypeError(
                "CapabilityCategory value must be a string"
            )

        normalized = value.strip().upper()

        if not normalized:
            raise ValueError(
                "CapabilityCategory value must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported CapabilityCategory: {value!r}"
            ) from exc


@dataclass(frozen=True, slots=True)
class CapabilityDefinition:
    """Single functional capability advertised by a NodeInstance."""

    name: str
    category: CapabilityCategory
    enabled: bool = True
    version: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError(
                "CapabilityDefinition.name must be a string"
            )

        normalized_name = self.name.strip().upper()

        if not normalized_name:
            raise ValueError(
                "CapabilityDefinition.name must not be empty"
            )

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )

        if not isinstance(self.category, CapabilityCategory):
            raise TypeError(
                "CapabilityDefinition.category must be "
                "a CapabilityCategory"
            )

        if not isinstance(self.enabled, bool):
            raise TypeError(
                "CapabilityDefinition.enabled must be a bool"
            )

        if self.version is not None:
            if not isinstance(self.version, str):
                raise TypeError(
                    "CapabilityDefinition.version must be "
                    "a string or None"
                )

            normalized_version = self.version.strip()

            object.__setattr__(
                self,
                "version",
                normalized_version or None,
            )

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class NodeCapability:
    """Collection of capabilities exposed by a NodeInstance."""

    capabilities: tuple[CapabilityDefinition, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.capabilities, tuple):
            raise TypeError(
                "NodeCapability.capabilities must be a tuple"
            )

        seen: set[str] = set()

        for capability in self.capabilities:
            if not isinstance(
                capability,
                CapabilityDefinition,
            ):
                raise TypeError(
                    "NodeCapability entries must be "
                    "CapabilityDefinition objects"
                )

            if capability.name in seen:
                raise ValueError(
                    f"Duplicate capability: {capability.name}"
                )

            seen.add(capability.name)

    @property
    def enabled(self) -> tuple[CapabilityDefinition, ...]:
        """Return all enabled capabilities."""
        return tuple(
            capability
            for capability in self.capabilities
            if capability.enabled
        )

    @property
    def disabled(self) -> tuple[CapabilityDefinition, ...]:
        """Return all disabled capabilities."""
        return tuple(
            capability
            for capability in self.capabilities
            if not capability.enabled
        )

    def supports(self, name: str) -> bool:
        """Return whether an enabled capability exists."""
        if not isinstance(name, str):
            raise TypeError(
                "capability name must be a string"
            )

        normalized = name.strip().upper()

        if not normalized:
            raise ValueError(
                "capability name must not be empty"
            )

        return any(
            capability.name == normalized
            and capability.enabled
            for capability in self.capabilities
        )

    def get(
        self,
        name: str,
    ) -> CapabilityDefinition | None:
        """Return capability definition by canonical name."""
        if not isinstance(name, str):
            raise TypeError(
                "capability name must be a string"
            )

        normalized = name.strip().upper()

        if not normalized:
            raise ValueError(
                "capability name must not be empty"
            )

        for capability in self.capabilities:
            if capability.name == normalized:
                return capability

        return None

    def __len__(self) -> int:
        return len(self.capabilities)

    def __contains__(self, name: object) -> bool:
        if not isinstance(name, str):
            return False

        return self.supports(name)
