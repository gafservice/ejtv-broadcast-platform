"""Pruebas del parser de teclado del dashboard."""

import pytest

from app.dashboard.models.dashboard_navigation_action import (
    DashboardNavigationAction,
)
from app.dashboard.services.dashboard_key_parser import (
    DashboardKeyParser,
)


@pytest.mark.parametrize(
    ("sequence", "expected"),
    (
        (b"\t", DashboardNavigationAction.NEXT_PANEL),
        (
            b"\x1b[Z",
            DashboardNavigationAction.PREVIOUS_PANEL,
        ),
        (
            b"\x1b[A",
            DashboardNavigationAction.SCROLL_UP,
        ),
        (
            b"\x1b[B",
            DashboardNavigationAction.SCROLL_DOWN,
        ),
        (
            b"\x1b[5~",
            DashboardNavigationAction.PAGE_UP,
        ),
        (
            b"\x1b[6~",
            DashboardNavigationAction.PAGE_DOWN,
        ),
        (b"\x1b[H", DashboardNavigationAction.HOME),
        (b"\x1b[F", DashboardNavigationAction.END),
        (b"q", DashboardNavigationAction.QUIT),
        (b"Q", DashboardNavigationAction.QUIT),
    ),
)
def test_parser_maps_terminal_sequences(
    sequence: bytes,
    expected: DashboardNavigationAction,
) -> None:
    parser = DashboardKeyParser()

    assert parser.parse(sequence) is expected


@pytest.mark.parametrize(
    "sequence",
    (
        b"",
        b"x",
        b" ",
        b"\x1b",
        b"\x1b[C",
        b"\x1b[D",
    ),
)
def test_parser_ignores_unknown_sequences(
    sequence: bytes,
) -> None:
    parser = DashboardKeyParser()

    assert parser.parse(sequence) is None


@pytest.mark.parametrize(
    "invalid",
    (
        None,
        "q",
        1,
        bytearray(b"q"),
    ),
)
def test_parser_rejects_non_bytes(
    invalid,
) -> None:
    parser = DashboardKeyParser()

    with pytest.raises(
        TypeError,
        match="sequence must be bytes",
    ):
        parser.parse(invalid)
