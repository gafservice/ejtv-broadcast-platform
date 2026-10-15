"""Contract for adaptive INCOMING vertical geometry."""

import pytest

from app.dashboard.services.incoming_vertical_geometry_policy import (
    IncomingVerticalGeometryPolicy,
)


@pytest.mark.parametrize(
    "signal_count",
    (0, 1, 2, 3),
)
def test_list_height_follows_actual_signal_count(signal_count):
    geometry = IncomingVerticalGeometryPolicy().calculate(
        terminal_height=40,
        signal_count=signal_count,
        maximum_visible_rows=8,
    )

    assert geometry.visible_rows == signal_count
    assert geometry.list_height == max(3, signal_count + 3)


def test_list_does_not_expand_to_fill_terminal():
    geometry = IncomingVerticalGeometryPolicy().calculate(
        terminal_height=50,
        signal_count=3,
        maximum_visible_rows=8,
    )

    assert geometry.list_height == 6
    assert geometry.detail_height > geometry.list_height


def test_list_respects_maximum_visible_rows():
    geometry = IncomingVerticalGeometryPolicy().calculate(
        terminal_height=50,
        signal_count=20,
        maximum_visible_rows=5,
    )

    assert geometry.visible_rows == 5
    assert geometry.list_height == 8


def test_geometry_preserves_terminal_budget():
    geometry = IncomingVerticalGeometryPolicy().calculate(
        terminal_height=40,
        signal_count=3,
        maximum_visible_rows=8,
    )

    assert (
        geometry.list_height
        + geometry.detail_height
        + geometry.header_height
        == 40
    )


def test_small_terminal_degrades_without_negative_heights():
    geometry = IncomingVerticalGeometryPolicy().calculate(
        terminal_height=12,
        signal_count=3,
        maximum_visible_rows=8,
    )

    assert geometry.list_height >= 0
    assert geometry.detail_height >= 0
    assert geometry.insufficient_height is True


@pytest.mark.parametrize(
    "terminal_height,signal_count,maximum_visible_rows",
    (
        (0, 3, 8),
        (-1, 3, 8),
        (40, -1, 8),
        (40, 3, 0),
    ),
)
def test_invalid_geometry_inputs_are_rejected(
    terminal_height,
    signal_count,
    maximum_visible_rows,
):
    with pytest.raises(ValueError):
        IncomingVerticalGeometryPolicy().calculate(
            terminal_height=terminal_height,
            signal_count=signal_count,
            maximum_visible_rows=maximum_visible_rows,
        )



def test_rich_measured_list_height_for_three_signals():
    """Three rows require six lines in the inspected Rich table."""
    geometry = IncomingVerticalGeometryPolicy().calculate(
        terminal_height=30,
        signal_count=3,
        maximum_visible_rows=8,
    )

    assert geometry.list_height == 6
    assert geometry.visible_rows == 3
    assert geometry.detail_height == 21


@pytest.mark.parametrize(
    "terminal_height,signal_count",
    (
        (12, 3),
        (12, 8),
        (16, 3),
        (16, 8),
    ),
)
def test_insufficient_height_preserves_detail_space(
    terminal_height,
    signal_count,
):
    """The list must not consume the entire compact detail area."""
    geometry = IncomingVerticalGeometryPolicy().calculate(
        terminal_height=terminal_height,
        signal_count=signal_count,
        maximum_visible_rows=8,
    )

    assert geometry.insufficient_height is True
    assert geometry.detail_height >= min(
        8,
        terminal_height - geometry.header_height,
    )


@pytest.mark.parametrize(
    "terminal_height",
    (12, 16, 20, 24, 30, 40),
)
def test_geometry_budget_is_always_preserved(terminal_height):
    """The policy must never allocate more than the terminal."""
    geometry = IncomingVerticalGeometryPolicy().calculate(
        terminal_height=terminal_height,
        signal_count=20,
        maximum_visible_rows=8,
    )

    assert (
        geometry.header_height
        + geometry.list_height
        + geometry.detail_height
        == terminal_height
    )

    assert geometry.list_height >= 0
    assert geometry.detail_height >= 0
    assert geometry.visible_rows >= 0


def test_zero_visible_rows_does_not_imply_zero_detail():
    """An insufficient list viewport must not hide all detail."""
    geometry = IncomingVerticalGeometryPolicy().calculate(
        terminal_height=12,
        signal_count=20,
        maximum_visible_rows=8,
    )

    assert geometry.insufficient_height is True
    assert geometry.detail_height > 0
