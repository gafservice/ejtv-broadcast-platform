"""Visual contract for INCOMING contextual detail tab strip."""

import pytest

from rich.text import Text

from app.dashboard.models.incoming_detail_tab_state import (
    IncomingDetailTab,
)

from app.dashboard.renderers.incoming_detail_tab_strip import (
    IncomingDetailTabStrip,
)


@pytest.mark.parametrize(
    "tab",
    tuple(IncomingDetailTab),
)
def test_all_tabs_can_be_active(tab):
    strip = IncomingDetailTabStrip()

    result = strip.render(
        active_tab=tab,
        width=120,
    )

    assert isinstance(result, Text)

    assert "SIGNAL" in result.plain
    assert "TRANSPORT" in result.plain
    assert "VIDEO" in result.plain
    assert "AUDIO" in result.plain
    assert "EVENTS" in result.plain
    assert "STATS" in result.plain

    assert len(result.plain) <= 120


def test_active_tab_has_distinct_style():
    strip = IncomingDetailTabStrip()

    result = strip.render(
        active_tab=IncomingDetailTab.VIDEO,
        width=120,
    )

    active_spans = [
        span
        for span in result.spans
        if "bold" in str(span.style)
    ]

    assert active_spans

    active_text = [
        result.plain[span.start:span.end]
        for span in active_spans
    ]

    assert any(
        "VIDEO" in value
        for value in active_text
    )


@pytest.mark.parametrize(
    "width",
    (55, 65, 75),
)
def test_intermediate_width_uses_compact_labels(width):
    strip = IncomingDetailTabStrip()

    result = strip.render(
        active_tab=IncomingDetailTab.TRANSPORT,
        width=width,
    )

    assert isinstance(result, Text)

    assert len(result.plain) <= width

    assert "1" in result.plain
    assert "2" in result.plain
    assert "3" in result.plain
    assert "4" in result.plain
    assert "5" in result.plain
    assert "6" in result.plain


@pytest.mark.parametrize(
    "width",
    (20, 25, 30),
)
def test_narrow_width_preserves_six_tab_numbers(width):
    strip = IncomingDetailTabStrip()

    result = strip.render(
        active_tab=IncomingDetailTab.STATISTICS,
        width=width,
    )

    assert isinstance(result, Text)

    assert len(result.plain) <= width

    for number in "123456":
        assert number in result.plain


def test_render_is_deterministic():
    strip = IncomingDetailTabStrip()

    first = strip.render(
        active_tab=IncomingDetailTab.AUDIO,
        width=80,
    )

    second = strip.render(
        active_tab=IncomingDetailTab.AUDIO,
        width=80,
    )

    assert first.plain == second.plain
    assert first.spans == second.spans


def test_invalid_width_is_rejected():
    strip = IncomingDetailTabStrip()

    with pytest.raises(ValueError):
        strip.render(
            active_tab=IncomingDetailTab.SIGNAL,
            width=0,
        )


def test_invalid_active_tab_is_rejected():
    strip = IncomingDetailTabStrip()

    with pytest.raises(TypeError):
        strip.render(
            active_tab="video",
            width=80,
        )
