"""System capacity provider for the NOC runtime.

ENG-013B — Node SDK

This infrastructure component translates SystemResources into
canonical NodeCapacity resources.

It describes quantifiable host capacity. It does not publish capacity
to a NodeInstance; that responsibility belongs to CapacityService.
"""

from __future__ import annotations

from app.domain.system import SystemResources
from app.noc.domain.node_capacity import (
    CapacityResource,
    NodeCapacity,
)


class SystemCapacityProvider:
    """Translate system resources into canonical NodeCapacity."""

    def collect(
        self,
        resources: SystemResources,
    ) -> NodeCapacity:
        """Build current host capacity from one system capture."""

        if not isinstance(resources, SystemResources):
            raise TypeError(
                "resources must be a SystemResources"
            )

        memory_available = max(
            resources.memory.total_bytes
            - resources.memory.used_bytes,
            0,
        )

        return NodeCapacity(
            resources=(
                CapacityResource(
                    resource="System Memory",
                    maximum=resources.memory.total_bytes,
                    allocated=resources.memory.used_bytes,
                    reserved=0,
                    available=memory_available,
                    unit="bytes",
                ),
                CapacityResource(
                    resource="System Storage",
                    maximum=resources.disk.total_bytes,
                    allocated=resources.disk.used_bytes,
                    reserved=0,
                    available=resources.disk.free_bytes,
                    unit="bytes",
                ),
            )
        )
