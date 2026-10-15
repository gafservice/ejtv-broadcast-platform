"""Integration contract for INCOMING detail tab strip."""

from dataclasses import replace

import pytest

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.dashboard.models.incoming_detail_tab_state import (
    IncomingDetailTab,
    IncomingDetailTabState,
)
from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)
from app.dashboard.renderers.dashboard_renderer import (
    DashboardRenderer,
)
from app.domain.streaming.health import HealthStatus

from tests.dashboard.test_dashboard_renderer import (
    build_dashboard_data,
)


def make_data():
    incoming = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="ejtv",
                source="UDP",
                protocol="UDP",
                status="ACTIVE",
                bitrate_receive_mbps=4.0,
                health_status=HealthStatus.HEALTHY,
            ),
            IncomingRowData(
                path_name="enlace",
                source="UDP",
                protocol="UDP",
                status="ACTIVE",
                bitrate_receive_mbps=6.0,
                health_status=HealthStatus.DEGRADED,
                alarm_count=2,
                alarm_severity="MAJOR",
            ),
        )
    )

    return replace(
        build_dashboard_data(),
        incoming=incoming,
    )


def render_detail(
    tab=IncomingDetailTab.SIGNAL,
    *,
    capacity=5,
    selected="enlace",
):
    renderer = DashboardRenderer()

    layout = renderer.render(
        make_data(),
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=IncomingSelectionState(
            selected_path_name=selected,
        ),
        incoming_detail_tab_state=IncomingDetailTabState(
            active_tab=tab,
        ),
        incoming_visible_capacity=capacity,
    )

    return layout, layout["incoming"]["signal_detail"].renderable


@pytest.mark.parametrize(
    "tab",
    tuple(IncomingDetailTab),
)
def test_each_tab_has_visible_navigation_subtitle(tab):
    _, detail = render_detail(tab)

    assert isinstance(detail, Panel)
    assert isinstance(detail.subtitle, Text)

    for number in "123456":
        assert number in detail.subtitle.plain


@pytest.mark.parametrize(
    "tab",
    tuple(IncomingDetailTab),
)
def test_active_tab_is_highlighted(tab):
    _, detail = render_detail(tab)

    assert isinstance(detail.subtitle, Text)

    highlighted = [
        detail.subtitle.plain[span.start:span.end]
        for span in detail.subtitle.spans
        if "bold" in str(span.style)
    ]

    assert highlighted

    expected_number = str(
        tuple(IncomingDetailTab).index(tab) + 1
    )

    assert any(
        expected_number in label
        for label in highlighted
    )


def test_signal_detail_table_remains_unchanged():
    _, detail = render_detail(IncomingDetailTab.SIGNAL)

    assert isinstance(detail.title, Text)
    assert "SIGNAL DETAIL" in detail.title.plain
    assert "enlace" in detail.title.plain
    assert "ACTIVE" in detail.title.plain
    assert "DEGRADED" in detail.title.plain
    assert isinstance(detail.renderable, Table)

    columns = detail.renderable.columns

    fields = dict(
        zip(
            tuple(columns[0].cells),
            tuple(columns[1].cells),
        )
    )

    assert fields["Path"] == "enlace"
    assert fields["Health Status"] == "DEGRADED"
    assert fields["Summary"] == "2 MAJOR"


@pytest.mark.parametrize(
    "tab",
    (
        IncomingDetailTab.TRANSPORT,
        IncomingDetailTab.VIDEO,
        IncomingDetailTab.AUDIO,
        IncomingDetailTab.EVENTS,
        IncomingDetailTab.STATISTICS,
    ),
)
def test_specialized_content_remains_unavailable(tab):
    _, detail = render_detail(tab)

    assert "N/A" in str(detail.renderable)


@pytest.mark.parametrize(
    "capacity,expected_height",
    (
        (5, 20),
        (0, 12),
    ),
)
def test_existing_detail_height_is_preserved(
    capacity,
    expected_height,
):
    layout, detail = render_detail(
        IncomingDetailTab.VIDEO,
        capacity=capacity,
    )

    assert layout["incoming"]["signal_detail"].size == expected_height
    assert isinstance(detail, Panel)


def test_selected_signal_is_not_changed_by_tab_rendering():
    _, detail = render_detail(
        IncomingDetailTab.EVENTS,
        selected="ejtv",
    )

    assert "ejtv" in str(detail.renderable)
    assert "enlace" not in str(detail.renderable)
