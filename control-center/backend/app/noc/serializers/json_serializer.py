"""Generic JSON serialization helpers for NCS domain objects.

ENG-013B — Node SDK
NCS reference: 23-SERIALIZATION.md
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class JsonSerializer:
    """Serialize NCS-compatible values into deterministic JSON.

    The serializer preserves domain meaning and canonical field names.
    It does not validate, mutate or apply business rules.
    """

    def to_primitive(self, value: Any) -> Any:
        """Convert a supported value into JSON-compatible primitives."""
        if value is None:
            return None

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, datetime):
            return self._serialize_datetime(value)

        if isinstance(value, MappingProxyType):
            return {
                str(key): self.to_primitive(item)
                for key, item in value.items()
            }

        if isinstance(value, Mapping):
            return {
                str(key): self.to_primitive(item)
                for key, item in value.items()
            }

        if isinstance(value, tuple):
            return [
                self.to_primitive(item)
                for item in value
            ]

        if isinstance(value, list):
            return [
                self.to_primitive(item)
                for item in value
            ]

        if is_dataclass(value):
            return {
                field.name: self.to_primitive(
                    getattr(value, field.name)
                )
                for field in fields(value)
            }

        if isinstance(
            value,
            (str, int, float, bool),
        ):
            return value

        raise TypeError(
            f"Unsupported JSON serialization type: "
            f"{type(value).__name__}"
        )

    def dumps(
        self,
        value: Any,
        *,
        indent: int | None = None,
    ) -> str:
        """Serialize an NCS value to deterministic JSON text."""
        primitive = self.to_primitive(value)

        return json.dumps(
            primitive,
            ensure_ascii=False,
            sort_keys=True,
            separators=(
                (",", ":")
                if indent is None
                else (",", ": ")
            ),
            indent=indent,
        )

    @staticmethod
    def _serialize_datetime(
        value: datetime,
    ) -> str:
        """Serialize UTC datetime using RFC 3339 / ISO 8601."""
        if value.tzinfo is None:
            raise ValueError(
                "Cannot serialize naive datetime"
            )

        offset = value.utcoffset()

        if (
            offset is None
            or offset.total_seconds() != 0
        ):
            raise ValueError(
                "NCS datetime values must be UTC"
            )

        utc_value = value.astimezone(
            timezone.utc
        )

        return (
            utc_value
            .isoformat()
            .replace("+00:00", "Z")
        )
