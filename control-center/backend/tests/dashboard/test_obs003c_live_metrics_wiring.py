"""OBS-003C: operational dashboard metrics composition contract.

Static inspection only. No dashboard execution or network access.
"""

import ast
from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[2]
    / "app/dashboard/live_monitor.py"
)


def test_live_monitor_wires_shared_transport_metrics() -> None:
    """The live dashboard must reuse one client/parser pair."""

    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))

    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "build_dashboard_application"
    ]

    assert len(functions) == 1

    function = functions[0]

    assignments = {}

    for node in ast.walk(function):
        if not isinstance(node, ast.Assign):
            continue

        if len(node.targets) != 1:
            continue

        target = node.targets[0]

        if isinstance(target, ast.Name):
            assignments[target.id] = node.value

    acquisition = assignments.get("metrics_acquisition_service")

    assert acquisition is not None, (
        "RED: live_monitor does not construct shared acquisition"
    )

    assert isinstance(acquisition, ast.Call)

    assert isinstance(acquisition.func, ast.Name)

    assert (
        acquisition.func.id
        == "MediaMTXMetricsAcquisitionService"
    )

    assert [
        ast.unparse(arg)
        for arg in acquisition.args
    ] == ["metrics_client", "metrics_parser"]

    producer = assignments.get("transport_quality_producer")

    assert producer is not None, (
        "RED: live_monitor does not construct transport producer"
    )

    assert isinstance(producer, ast.Call)

    assert isinstance(producer.func, ast.Name)

    assert producer.func.id == "TransportQualityProducer"

    assert producer.args == []
    assert producer.keywords == []

    applications = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "DashboardApplication"
    ]

    assert len(applications) == 1

    kwargs = {
        keyword.arg: ast.unparse(keyword.value)
        for keyword in applications[0].keywords
    }

    assert (
        kwargs.get("metrics_acquisition_service")
        == "metrics_acquisition_service"
    )

    assert (
        kwargs.get("transport_quality_producer")
        == "transport_quality_producer"
    )

    assert kwargs.get("metrics_client") == "metrics_client"
    assert kwargs.get("metrics_parser") == "metrics_parser"
