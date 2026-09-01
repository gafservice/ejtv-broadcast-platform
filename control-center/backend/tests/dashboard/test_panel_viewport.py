import pytest

from app.dashboard.models.panel_viewport import PanelViewport


def test_defaults() -> None:
    viewport = PanelViewport()

    assert viewport.offset == 0
    assert viewport.page_size == 5


def test_rejects_negative_offset() -> None:
    with pytest.raises(
        ValueError,
        match="offset must not be negative",
    ):
        PanelViewport(offset=-1)


def test_rejects_zero_page_size() -> None:
    with pytest.raises(
        ValueError,
        match="page_size must be greater than zero",
    ):
        PanelViewport(page_size=0)


def test_rejects_bool_values() -> None:
    with pytest.raises(TypeError):
        PanelViewport(offset=True)

    with pytest.raises(TypeError):
        PanelViewport(page_size=True)


def test_bounds_first_page() -> None:
    viewport = PanelViewport(
        offset=0,
        page_size=5,
    )

    assert viewport.bounds(12) == (0, 5)


def test_bounds_middle_page() -> None:
    viewport = PanelViewport(
        offset=4,
        page_size=5,
    )

    assert viewport.bounds(12) == (4, 9)


def test_bounds_normalizes_offset_after_collection_shrinks() -> None:
    viewport = PanelViewport(
        offset=20,
        page_size=5,
    )

    assert viewport.bounds(7) == (2, 7)


def test_bounds_empty_collection() -> None:
    viewport = PanelViewport(
        offset=10,
        page_size=5,
    )

    assert viewport.bounds(0) == (0, 0)


def test_move_down_one_row() -> None:
    viewport = PanelViewport(
        offset=0,
        page_size=5,
    )

    moved = viewport.move(
        1,
        total_items=12,
    )

    assert moved.offset == 1


def test_move_does_not_pass_end() -> None:
    viewport = PanelViewport(
        offset=6,
        page_size=5,
    )

    moved = viewport.move(
        10,
        total_items=12,
    )

    assert moved.offset == 7


def test_move_does_not_pass_start() -> None:
    viewport = PanelViewport(
        offset=3,
        page_size=5,
    )

    moved = viewport.move(
        -10,
        total_items=12,
    )

    assert moved.offset == 0


def test_page_down() -> None:
    viewport = PanelViewport(
        offset=0,
        page_size=5,
    )

    moved = viewport.page_down(
        total_items=20,
    )

    assert moved.offset == 5


def test_page_up() -> None:
    viewport = PanelViewport(
        offset=8,
        page_size=5,
    )

    moved = viewport.page_up(
        total_items=20,
    )

    assert moved.offset == 3


def test_home() -> None:
    viewport = PanelViewport(
        offset=8,
        page_size=5,
    )

    moved = viewport.home()

    assert moved.offset == 0
    assert moved.page_size == 5


def test_end() -> None:
    viewport = PanelViewport(
        offset=0,
        page_size=5,
    )

    moved = viewport.end(
        total_items=23,
    )

    assert moved.offset == 18


def test_end_when_collection_smaller_than_page() -> None:
    viewport = PanelViewport(
        offset=0,
        page_size=5,
    )

    moved = viewport.end(
        total_items=3,
    )

    assert moved.offset == 0


@pytest.mark.parametrize(
    "total_items",
    [
        -1,
        True,
        1.5,
    ],
)
def test_rejects_invalid_total_items(
    total_items,
) -> None:
    viewport = PanelViewport()

    with pytest.raises(
        (TypeError, ValueError),
    ):
        viewport.bounds(total_items)
