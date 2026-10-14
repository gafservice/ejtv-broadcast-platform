"""Contract tests for canonical Duration in SIGNAL DETAIL."""

from datetime import datetime, timedelta, timezone

import pytest

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.renderers.incoming_panel_renderer import (
    IncomingPanelRenderer,
)
from app.dashboard.renderers.signal_detail_renderer import (
    SignalDetailRenderer,
)


REFERENCE_AT = datetime(
    2026, 10, 14, 20, 0, 0,
    tzinfo=timezone.utc,
)


def detail_fields(data):
    panel = SignalDetailRenderer().render(
        data,
        selected_path_name="ejtv",
    )

    table = panel.renderable

    return dict(
        zip(
            tuple(table.columns[0].cells),
            tuple(table.columns[1].cells),
        )
    )


def make_data(health_since, reference_at):
    row = IncomingRowData(
        path_name="ejtv",
        source="publisher",
        status="ACTIVE",
        bitrate_receive_mbps=4.7,
        health_status=None,
        protocol="UDP",
        remote_address="10.0.18.51:3000",
        health_since=health_since,
    )

    return IncomingPanelData(
        rows=(row,),
        reference_at=reference_at,
    )


def test_detail_duration_matches_canonical_formatter():
    since = REFERENCE_AT - timedelta(
        hours=2,
        minutes=15,
        seconds=30,
    )

    data = make_data(since, REFERENCE_AT)

    fields = detail_fields(data)

    expected = IncomingPanelRenderer._format_health_duration(
        health_since=since,
        reference_at=REFERENCE_AT,
    )

    assert fields["Duration"] == expected
    assert fields["Duration"] == "02:15:30"


@pytest.mark.parametrize(
    "since,reference",
    [
        (None, REFERENCE_AT),
        (REFERENCE_AT, None),
        (None, None),
        (
            REFERENCE_AT + timedelta(seconds=10),
            REFERENCE_AT,
        ),
    ],
)
def test_detail_duration_missing_or_invalid_is_na(
    since,
    reference,
):
    data = make_data(since, reference)

    fields = detail_fields(data)

    assert fields["Duration"] == "N/A"
