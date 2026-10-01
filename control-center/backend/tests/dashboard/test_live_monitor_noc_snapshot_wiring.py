"""Contract for canonical NOC snapshot wiring in live_monitor.

ENG-013C — Terminal Dashboard

The terminal monitor already owns a local NOC registry and performs one
system capture per dashboard cycle.  build_dashboard_application() must
wire a NocSnapshotProjection into DashboardApplication so that canonical
NOC telemetry consumes that same capture.

This contract does not permit HTTP/JWT wiring, a second registry, or a
second system capture.
"""

from __future__ import annotations

from app.dashboard.application import NocSnapshotProjection
from app.dashboard.live_monitor import build_dashboard_application


def test_live_monitor_wires_canonical_noc_snapshot_projection() -> None:
    """The production terminal application must own a NOC projection."""

    application = build_dashboard_application()

    projection = application._noc_snapshot_projection

    assert isinstance(
        projection,
        NocSnapshotProjection,
    )


def test_live_monitor_noc_projection_reuses_application_identity() -> None:
    """Projection and dashboard must target the same NOC identity."""

    application = build_dashboard_application()

    projection = application._noc_snapshot_projection

    assert projection is not None

    assert projection._node_id is application._node_id
    assert projection._instance_id is application._instance_id


def test_live_monitor_noc_projection_uses_canonical_services() -> None:
    """Projection must be backed by existing NOC service contracts."""

    application = build_dashboard_application()

    projection = application._noc_snapshot_projection

    assert projection is not None

    from app.noc.runtime.telemetry_refresh import (
        TelemetryRefreshService,
    )
    from app.noc.services.snapshot_service import (
        SnapshotService,
    )

    assert isinstance(
        projection._telemetry_refresh_service,
        TelemetryRefreshService,
    )

    assert isinstance(
        projection._snapshot_service,
        SnapshotService,
    )
