"""Presentation model for canonical NOC capacity."""

from dataclasses import dataclass
from datetime import datetime

from app.noc.domain.node_capacity import NodeCapacity


@dataclass(frozen=True)
class CapacityResourceRowData:
    """Presentation row for one canonical capacity resource."""

    resource: str
    maximum: float
    allocated: float
    reserved: float
    available: float
    unit: str
    utilization_percent: float


@dataclass(frozen=True)
class CapacityPanelData:
    """Presentation projection of canonical NodeCapacity."""

    resources: tuple[CapacityResourceRowData, ...]
    captured_at: datetime

    @classmethod
    def from_capacity(
        cls,
        capacity: NodeCapacity,
        *,
        captured_at: datetime,
    ) -> "CapacityPanelData":
        return cls(
            resources=tuple(
                CapacityResourceRowData(
                    resource=resource.resource,
                    maximum=resource.maximum,
                    allocated=resource.allocated,
                    reserved=resource.reserved,
                    available=resource.available,
                    unit=resource.unit,
                    utilization_percent=(
                        resource.utilization_percent
                    ),
                )
                for resource in capacity.resources
            ),
            captured_at=captured_at,
        )
