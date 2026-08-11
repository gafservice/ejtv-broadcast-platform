"""Canonical functional classification for a NOC Node.

ENG-013B — Node SDK
NCS reference: 08-NODE-TYPE.md
"""

from __future__ import annotations

from enum import Enum


class NodeType(str, Enum):
    """Canonical functional type of a Node.

    A NodeType describes the architectural responsibility of a Node.
    It does not describe implementation, infrastructure, health,
    availability, capacity or runtime state.
    """

    IDENTITY = "IDENTITY"
    STREAMING = "STREAMING"
    TRANSCODING = "TRANSCODING"
    METRICS = "METRICS"
    ALARM = "ALARM"
    AUTOMATION = "AUTOMATION"
    STORAGE = "STORAGE"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    EDGE = "EDGE"
    SYSTEM = "SYSTEM"

    def __str__(self) -> str:
        """Return the canonical value."""
        return self.value

    @classmethod
    def from_value(cls, value: str) -> "NodeType":
        """Build a NodeType from a canonical string value.

        Leading and trailing whitespace are ignored, but the canonical
        representation remains uppercase as defined by the NCS.
        """
        if not isinstance(value, str):
            raise TypeError("NodeType value must be a string")

        normalized = value.strip().upper()

        if not normalized:
            raise ValueError("NodeType value must not be empty")

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported NodeType: {value!r}"
            ) from exc
