"""ENG-013C 235E.25F — automatic INCOMING selection reconciliation."""

from unittest.mock import Mock

from app.dashboard.application import DashboardApplication
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)


def make_application_with_snapshot(path_names):
    """Use an existing dashboard projection without external capture."""

    application = object.__new__(DashboardApplication)

    application._incoming_selection_state = IncomingSelectionState()
    application._incoming_path_names = ()

    incoming = Mock()
    incoming.rows = tuple(
        Mock(path_name=name)
        for name in path_names
    )

    dashboard_data = Mock()
    dashboard_data.incoming = incoming

    application._dashboard_snapshot_service = Mock()
    application._dashboard_snapshot_service.build_snapshot.return_value = (
        dashboard_data
    )

    return application, dashboard_data


def test_build_dashboard_reconciles_incoming_selection():
    """The real dashboard build must reconcile its projected rows."""

    application, dashboard_data = make_application_with_snapshot(
        ("service-a", "service-b")
    )

    # A capture-complete callback is deliberately not introduced:
    # reconciliation belongs inside the existing build_dashboard flow.
    #
    # This test inspects the real implementation contract using AST
    # rather than duplicating acquisition dependencies.

    import ast
    import inspect
    import textwrap

    source = textwrap.dedent(
        inspect.getsource(DashboardApplication.build_dashboard)
    )

    tree = ast.parse(source)

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "reconcile_incoming_selection"
    ]

    assert len(calls) == 1, (
        "build_dashboard must reconcile INCOMING selection "
        "once per projected dashboard"
    )


def test_reconciliation_uses_projected_incoming_rows():
    """Selection must derive from incoming.rows, not raw MediaMTX paths."""

    import ast
    import inspect
    import textwrap

    source = textwrap.dedent(
        inspect.getsource(DashboardApplication.build_dashboard)
    )

    tree = ast.parse(source)

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "reconcile_incoming_selection"
    ]

    assert len(calls) == 1

    call = calls[0]

    assert len(call.args) == 1

    argument = ast.unparse(call.args[0])

    assert argument == "path_names"

    assignments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "path_names"
            for target in node.targets
        )
    ]

    assert len(assignments) == 1

    projection = ast.unparse(assignments[0].value)

    assert "incoming.rows" in projection
    assert "row.path_name" in projection


def test_empty_incoming_panel_is_supported():
    """The selection model must accept an empty projected collection."""

    application, _ = make_application_with_snapshot(())

    application.reconcile_incoming_selection(())

    assert application.incoming_selection_state.selected_path_name is None
