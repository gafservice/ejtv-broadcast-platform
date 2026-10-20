"""Transport Quality observation forwarding contract.

ENG-013C — 235E.30A — 9A.68.7D.4.

Presentation routing only. No metric attribution or Health inference.
"""

from dataclasses import replace
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from rich.panel import Panel

from app.dashboard.models.incoming_detail_tab_state import (
    IncomingDetailTab,
    IncomingDetailTabState,
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
from app.dashboard.renderers.incoming_transport_cards_renderer import (
    IncomingTransportCardsRenderer,
)
from app.domain.streaming.media_observation import (
    EvidenceAvailability,
)
from app.domain.streaming.transport_quality_observation import (
    TransportQualityObservation,
)
from tests.dashboard.test_incoming_transport_tab_integration import (
    make_dashboard,
)


@pytest.mark.parametrize(
    "selected_path_name,compact",
    (
        ("ejtv", False),
        ("impact", False),
        ("ejtv", True),
        ("impact", True),
    ),
)
def test_transport_tab_forwards_observations_without_rewriting_identity(
    selected_path_name,
    compact,
):
    observations = (
        TransportQualityObservation(
            service_id="ejtv",
            path_name="ejtv",
            source_type="udpSource",
            observed_at=datetime(
                2026, 10, 20, 18, 0, tzinfo=timezone.utc
            ),
            availability=EvidenceAvailability.UNAVAILABLE,
        ),
        TransportQualityObservation(
            service_id="impact",
            path_name="impact",
            source_type="srtConn",
            observed_at=datetime(
                2026, 10, 20, 18, 0, tzinfo=timezone.utc
            ),
            availability=EvidenceAvailability.UNAVAILABLE,
        ),
    )

    dashboard_data = replace(
        make_dashboard(),
        transport_quality_observations=observations,
    )

    original_render = IncomingTransportCardsRenderer.render
    captured = []

    def observe_render(self, data, **kwargs):
        captured.append(kwargs.copy())

        # Preserve existing rendering behavior while inspecting the route.
        kwargs.pop("transport_quality_observations", None)

        return original_render(
            self,
            data,
            **kwargs,
        )

    with patch.object(
        IncomingTransportCardsRenderer,
        "render",
        observe_render,
    ):
        renderer = DashboardRenderer()

        render_kwargs = {
            "terminal_navigation_state": TerminalNavigationState(
                active_view=TerminalView.INCOMING,
            ),
            "incoming_selection_state": IncomingSelectionState(
                selected_path_name=selected_path_name,
            ),
            "incoming_detail_tab_state": IncomingDetailTabState(
                active_tab=IncomingDetailTab.TRANSPORT,
            ),
            "incoming_visible_capacity": 5,
        }

        if compact:
            # Height below 20 selects the compact transport path.
            from app.dashboard.services.incoming_vertical_geometry_policy import (
                IncomingVerticalGeometry,
            )

            render_kwargs["incoming_vertical_geometry"] = (
                IncomingVerticalGeometry(
                    header_height=3,
                    list_height=5,
                    detail_height=12,
                    visible_rows=5,
                    insufficient_height=False,
                )
            )

        layout = renderer.render(
            dashboard_data,
            **render_kwargs,
        )

    assert isinstance(
        layout["incoming"]["signal_detail"].renderable,
        Panel,
    )

    assert len(captured) == 1

    forwarded = captured[0]

    assert forwarded["selected_path_name"] == selected_path_name
    assert forwarded["compact"] is compact

    assert (
        forwarded.get("transport_quality_observations")
        is observations
    )
