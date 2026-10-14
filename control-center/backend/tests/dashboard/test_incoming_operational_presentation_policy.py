"""Contract tests for the operational INCOMING presentation mode."""

import pytest

from app.dashboard.services.incoming_presentation_policy import (
    IncomingPresentationPolicy,
)


@pytest.mark.parametrize(
    ("width", "expected_mode"),
    [
        (80, "compact"),
        (99, "compact"),
        (100, "operational"),
        (119, "operational"),
        (120, "operational"),
        (122, "operational"),
        (139, "operational"),
        (140, "full"),
        (160, "full"),
    ],
)
def test_incoming_presentation_selects_mode_by_width(
    width,
    expected_mode,
):
    result = IncomingPresentationPolicy().calculate(
        terminal_width=width,
        incoming_height=7,
    )

    assert result.mode == expected_mode
    assert result.page_size == 4
