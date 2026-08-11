"""Quantifiable capacity exposed by a NodeInstance.

ENG-013B — Node SDK
NCS reference: 15-NODE-CAPACITY.md
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from numbers import Real


CapacityValue = int | float


@dataclass(frozen=True, slots=True)
class CapacityResource:
    """Single quantifiable capacity resource of a NodeInstance.

    A CapacityResource describes installed, allocated, reserved and
    currently available capacity for one canonical resource.
    """

    resource: str
    maximum: CapacityValue
    allocated: CapacityValue
    reserved: CapacityValue
    available: CapacityValue
    unit: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "resource",
            self._normalize_required_string(
                self.resource,
                "resource",
            ),
        )

        object.__setattr__(
            self,
            "unit",
            self._normalize_required_string(
                self.unit,
                "unit",
            ),
        )

        for field_name in (
            "maximum",
            "allocated",
            "reserved",
            "available",
        ):
            value = getattr(self, field_name)
            self._validate_numeric_value(
                value,
                field_name,
            )

        if self.allocated > self.maximum:
            raise ValueError(
                "CapacityResource.allocated must not exceed maximum"
            )

        if self.reserved > self.maximum:
            raise ValueError(
                "CapacityResource.reserved must not exceed maximum"
            )

        if self.available > self.maximum:
            raise ValueError(
                "CapacityResource.available must not exceed maximum"
            )

        committed = (
            self.allocated
            + self.reserved
            + self.available
        )

        if committed > self.maximum:
            raise ValueError(
                "CapacityResource allocated + reserved + available "
                "must not exceed maximum"
            )

    @property
    def committed(self) -> CapacityValue:
        """Return allocated plus reserved capacity."""
        return self.allocated + self.reserved

    @property
    def utilization(self) -> float:
        """Return allocated capacity as a fraction of maximum.

        This is a derived convenience value, not a NodeMetric.
        """
        if self.maximum == 0:
            return 0.0

        return float(self.allocated / self.maximum)

    @property
    def utilization_percent(self) -> float:
        """Return allocated capacity as percentage of maximum."""
        return self.utilization * 100.0

    @property
    def has_available_capacity(self) -> bool:
        """Return whether capacity exists for new assignments."""
        return self.available > 0

    @staticmethod
    def _normalize_required_string(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"CapacityResource.{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"CapacityResource.{field_name} must not be empty"
            )

        return normalized

    @staticmethod
    def _validate_numeric_value(
        value: CapacityValue,
        field_name: str,
    ) -> None:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(
                f"CapacityResource.{field_name} "
                "must be a real number"
            )

        if not isfinite(float(value)):
            raise ValueError(
                f"CapacityResource.{field_name} must be finite"
            )

        if value < 0:
            raise ValueError(
                f"CapacityResource.{field_name} "
                "must not be negative"
            )

    def __str__(self) -> str:
        return self.resource


@dataclass(frozen=True, slots=True)
class NodeCapacity:
    """Collection of capacity resources exposed by a NodeInstance."""

    resources: tuple[CapacityResource, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.resources, tuple):
            raise TypeError(
                "NodeCapacity.resources must be a tuple"
            )

        seen: set[str] = set()

        for resource in self.resources:
            if not isinstance(resource, CapacityResource):
                raise TypeError(
                    "NodeCapacity entries must be "
                    "CapacityResource objects"
                )

            canonical_name = resource.resource.casefold()

            if canonical_name in seen:
                raise ValueError(
                    f"Duplicate capacity resource: "
                    f"{resource.resource}"
                )

            seen.add(canonical_name)

    def get(
        self,
        resource: str,
    ) -> CapacityResource | None:
        """Return a resource by canonical name."""
        normalized = self._normalize_resource_name(resource)

        for item in self.resources:
            if item.resource.casefold() == normalized.casefold():
                return item

        return None

    def has_resource(
        self,
        resource: str,
    ) -> bool:
        """Return whether a resource exists."""
        return self.get(resource) is not None

    def available_for(
        self,
        resource: str,
    ) -> CapacityValue | None:
        """Return available capacity for a resource."""
        item = self.get(resource)

        if item is None:
            return None

        return item.available

    def __len__(self) -> int:
        return len(self.resources)

    def __contains__(self, resource: object) -> bool:
        if not isinstance(resource, str):
            return False

        return self.has_resource(resource)

    @staticmethod
    def _normalize_resource_name(resource: str) -> str:
        if not isinstance(resource, str):
            raise TypeError(
                "resource name must be a string"
            )

        normalized = resource.strip()

        if not normalized:
            raise ValueError(
                "resource name must not be empty"
            )

        return normalized
