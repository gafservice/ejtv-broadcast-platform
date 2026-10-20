"""Transport quality selector integration with INCOMING renderer.

ENG-013C — 235E.30A — 9A.68.7D.10.

Tests selection identity only. No metric attribution or Health changes.
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
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


OBSERVED_AT = datetime(2026, 10, 20, 18, 0, tzinfo=timezone.utc)


def make_observation(name, source_type):
    return TransportQualityObservation(
        service_id=name,
        path_name=name,
        source_type=source_type,
        observed_at=OBSERVED_AT,
        availability=EvidenceAvailability.UNAVAILABLE,
    )


def make_row(name, source_type):
    return IncomingRowData(
        path_name=name,
        source="test",
        status="ready",
        bitrate_receive_mbps=None,
        health_status=None,
        transport_source_type=source_type,
    )


@pytest.mark.parametrize("compact", (False, True))
@pytest.mark.parametrize(
    "selected_path,source_type",
    (
        ("ejtv", "udpSource"),
        ("enlace", "udpSource"),
        ("impact", "srtConn"),
    ),
)
def test_render_selects_matching_observation(
    selected_path,
    source_type,
    compact,
):
    observations = (
        make_observation("ejtv", "udpSource"),
        make_observation("enlace", "udpSource"),
        make_observation("impact", "srtConn"),
    )

    data = IncomingPanelData(
        rows=(
            make_row("ejtv", "udpSource"),
            make_row("enlace", "udpSource"),
            make_row("impact", "srtConn"),
        ),
        reference_at=OBSERVED_AT,
    )

    original = (
        IncomingTransportCardsRenderer
        ._select_transport_quality_observation
    )

    calls = []

    def spy(
        observations_arg,
        *,
        path_name,
        source_type,
        source_id,
    ):
        calls.append(
            (observations_arg, path_name, source_type, source_id)
        )
        return original(
            observations_arg,
            path_name=path_name,
            source_type=source_type,
            source_id=source_id,
        )

    with patch.object(
        IncomingTransportCardsRenderer,
        "_select_transport_quality_observation",
        staticmethod(spy),
    ):
        IncomingTransportCardsRenderer().render(
            data,
            selected_path_name=selected_path,
            compact=compact,
            transport_quality_observations=observations,
        )

    assert len(calls) == 1
    assert calls[0][0] is observations
    assert calls[0][1] == selected_path
    assert calls[0][2] == source_type
    assert calls[0][3] is None


@pytest.mark.parametrize("compact", (False, True))
def test_render_without_selected_path_does_not_select_evidence(compact):
    observations = (
        make_observation("ejtv", "udpSource"),
    )

    data = IncomingPanelData(
        rows=(make_row("ejtv", "udpSource"),),
        reference_at=OBSERVED_AT,
    )

    with patch.object(
        IncomingTransportCardsRenderer,
        "_select_transport_quality_observation",
    ) as selector:
        IncomingTransportCardsRenderer().render(
            data,
            selected_path_name=None,
            compact=compact,
            transport_quality_observations=observations,
        )

    selector.assert_not_called()
