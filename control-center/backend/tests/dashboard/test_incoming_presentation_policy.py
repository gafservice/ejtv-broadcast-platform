"""Contract tests for adaptive INCOMING presentation policy."""

import pytest

from app.dashboard.services.incoming_presentation_policy import (
    IncomingPresentationPolicy,
)


@pytest.mark.parametrize(
    "width,height,expected_mode,expected_page_size",
    [
        (80, 7, "compact", 4),
        (100, 7, "operational", 4),
        (120, 17, "operational", 14),
        (160, 27, "full", 24),
    ],
)
def test_policy_selects_mode_and_capacity(
    width,
    height,
    expected_mode,
    expected_page_size,
):
    """Presentation capacity follows the available region."""

    result = IncomingPresentationPolicy().calculate(
        terminal_width=width,
        incoming_height=height,
    )

    assert result.mode == expected_mode
    assert result.page_size == expected_page_size


def test_policy_does_not_depend_on_signal_count():
    """Presentation capacity is independent of capture volume."""

    policy = IncomingPresentationPolicy()

    result = policy.calculate(
        terminal_width=100,
        incoming_height=7,
    )

    assert result.page_size == 4


def test_policy_rejects_invalid_width():
    """Terminal width must be positive."""

    with pytest.raises(ValueError):
        IncomingPresentationPolicy().calculate(
            terminal_width=0,
            incoming_height=7,
        )


def test_policy_rejects_invalid_height():
    """INCOMING height must be positive."""

    with pytest.raises(ValueError):
        IncomingPresentationPolicy().calculate(
            terminal_width=100,
            incoming_height=0,
        )


def test_policy_handles_minimum_panel_height():
    """A region without row space has zero visible capacity."""

    result = IncomingPresentationPolicy().calculate(
        terminal_width=100,
        incoming_height=3,
    )

    assert result.mode == "operational"
    assert result.page_size == 0


def test_policy_does_not_require_rich_console():
    """Policy must operate without a Rich console instance."""

    result = IncomingPresentationPolicy().calculate(
        terminal_width=100,
        incoming_height=7,
    )

    assert result.mode == "operational"
    assert result.page_size == 4
