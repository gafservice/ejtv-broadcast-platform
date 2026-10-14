"""Signal Detail tables must keep labels near their values."""

from datetime import datetime, timezone

import pytest

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.renderers.signal_detail_renderer import (
    SignalDetailRenderer,
)


@pytest.mark.parametrize("compact", [False, True])
def test_signal_detail_does_not_expand_field_value_columns(compact):
    row = IncomingRowData(
        path_name="ejtv",
        source="MPEG-TS",
        protocol="UDP",
        remote_address="10.0.18.51:3000",
        bitrate_receive_mbps=4.94,
        status="ACTIVE",
        health_status=None,
    )

    data = IncomingPanelData(
        rows=(row,),
        reference_at=datetime.now(timezone.utc),
    )

    panel = SignalDetailRenderer().render(
        data,
        selected_path_name="ejtv",
        compact=compact,
    )

    assert panel.renderable.expand is False
