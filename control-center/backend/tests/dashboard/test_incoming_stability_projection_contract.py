"""Offline contract tests for incoming stability projection."""

from dataclasses import fields
from inspect import signature
from pathlib import Path

from app.dashboard.models.incoming_panel import IncomingRowData
from app.dashboard.services.dashboard_service import DashboardService
from app.dashboard.services.dashboard_snapshot_service import (
    DashboardSnapshotInput,
    DashboardSnapshotService,
)
from app.dashboard.services.incoming_path_stability_tracker import (
    IncomingPathStability,
)


def test_incoming_row_exposes_stability_fields():
    names = {field.name for field in fields(IncomingRowData)}

    assert "transport_observed_interruptions" in names
    assert "transport_observed_recoveries" in names


def test_snapshot_input_accepts_stability_mapping():
    names = {field.name for field in fields(DashboardSnapshotInput)}

    assert "incoming_path_stability" in names


def test_dashboard_service_accepts_stability_mapping():
    for method in (
        DashboardService.build_incoming_panel,
        DashboardService.build_dashboard_from_measurement,
    ):
        assert "incoming_path_stability" in signature(method).parameters


def test_stability_values_are_independent():
    values = {
        "impact": IncomingPathStability(
            interruptions=2,
            recoveries=1,
        ),
        "ejtv": IncomingPathStability(
            interruptions=0,
            recoveries=0,
        ),
        "enlace": IncomingPathStability(
            interruptions=3,
            recoveries=2,
        ),
    }

    assert values["impact"].interruptions == 2
    assert values["ejtv"].interruptions == 0
    assert values["enlace"].recoveries == 2


def test_snapshot_service_forwards_stability_mapping():
    class RecordingDashboardService:
        def __init__(self):
            self.kwargs = None

        def build_dashboard_from_measurement(self, **kwargs):
            self.kwargs = kwargs
            return "sentinel"

    recording = RecordingDashboardService()
    coordinator = DashboardSnapshotService(recording)

    values = {
        "impact": IncomingPathStability(
            interruptions=2,
            recoveries=1,
        )
    }

    class SnapshotInputStub:
        def __getattr__(self, name):
            if name == "incoming_path_stability":
                return values
            return None

    result = coordinator.build_snapshot(SnapshotInputStub())

    assert result == "sentinel"
    assert recording.kwargs["incoming_path_stability"] is values


def test_application_projects_candidate_mapping():
    source = Path(
        "app/dashboard/application.py"
    ).read_text()

    assert "incoming_path_stability[path.name]" in source
    assert "stability_candidate.observe(" in source
    assert "'incoming_path_stability'" in source


def test_dashboard_service_projects_row_values():
    source = Path(
        "app/dashboard/services/dashboard_service.py"
    ).read_text()

    assert "transport_observed_interruptions=(" in source
    assert "transport_observed_recoveries=(" in source
    assert "incoming_path_stability[media_path.name]" in source
