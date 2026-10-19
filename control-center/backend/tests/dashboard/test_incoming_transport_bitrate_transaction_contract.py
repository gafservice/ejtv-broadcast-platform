"""Structural RED contracts for transactional INCOMING bitrate wiring."""

import ast
import inspect
import textwrap

from app.dashboard.application import DashboardApplication


def _method_tree():
    source = textwrap.dedent(
        inspect.getsource(DashboardApplication.build_dashboard)
    )
    tree = ast.parse(source)

    assert len(tree.body) == 1
    assert isinstance(tree.body[0], ast.FunctionDef)

    return tree.body[0]


def _calls(method, name):
    return [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name)
            and node.func.id == name
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == name
        )
    ]


def _persistent_window_assignments(method):
    return [
        node
        for node in ast.walk(method)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets
            if isinstance(node, ast.Assign)
            else [node.target]
        )
        if isinstance(target, ast.Attribute)
        and target.attr == "_incoming_transport_bitrate_window"
        and isinstance(target.value, ast.Name)
        and target.value.id == "self"
    ]


def test_build_dashboard_prepares_independent_window_candidate():
    method = _method_tree()

    assert _calls(method, "deepcopy"), (
        "RED: build_dashboard must prepare an independent "
        "candidate before updating rolling bitrate history."
    )


def test_build_dashboard_forwards_bitrate_statistics():
    method = _method_tree()

    snapshot_inputs = _calls(method, "DashboardSnapshotInput")

    assert len(snapshot_inputs) == 1

    # The current application uses a kwargs dictionary.
    # The contract requires that the statistics key be
    # explicitly prepared within the method.
    statistics_key = "incoming_transport_bitrate_statistics"

    has_statistics_key = any(
        isinstance(node, ast.Constant)
        and node.value == statistics_key
        for node in ast.walk(method)
    )

    assert has_statistics_key, (
        "RED: DashboardSnapshotInput must receive "
        "rolling bitrate statistics."
    )


def test_build_dashboard_has_window_commit_after_snapshot_build():
    method = _method_tree()

    snapshot_calls = _calls(method, "build_snapshot")
    assignments = _persistent_window_assignments(method)

    assert len(snapshot_calls) == 1

    assert assignments, (
        "RED: successful dashboard construction must "
        "commit the candidate bitrate window."
    )

    assert all(
        assignment.lineno > snapshot_calls[0].lineno
        for assignment in assignments
    ), (
        "RED: bitrate window must not be committed "
        "before build_snapshot."
    )
