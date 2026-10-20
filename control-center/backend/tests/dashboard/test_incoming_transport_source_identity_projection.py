"""Incoming source identity projection contract.

ENG-013C — 235E.30A — 9A.68.7D.28.

Preserve MediaMTX source identity in presentation data.
No RTT attribution, Health evaluation, or metric rendering.
"""

from dataclasses import fields

import pytest

from app.dashboard.models.incoming_panel import IncomingRowData
from app.domain.streaming.health import HealthStatus
from app.domain.streaming.models import MediaSource

from tests.dashboard.test_incoming_transport_data_projection import (
    build_panel,
    make_path,
)


@pytest.mark.parametrize(
    "source_type,source_id",
    (
        ("srtSource", "impact-source"),
        ("mpegtsSource", "ejtv-source"),
        ("srtConn", "publisher-A"),
        ("udpSource", "udp-source"),
        ("srtSource", None),
        ("mpegtsSource", None),
    ),
)
def test_projects_exact_mediamtx_source_identity(
    source_type,
    source_id,
):
    from dataclasses import replace

    path = make_path()
    path = replace(
        path,
        source=MediaSource(
            source_type=source_type,
            source_id=source_id,
        ),
    )

    row = build_panel(media_path=path).rows[0]

    assert row.transport_source_type == source_type
    assert row.transport_source_id == source_id


def test_incoming_row_contract_exposes_optional_source_identity():
    names = {item.name for item in fields(IncomingRowData)}

    assert "transport_source_id" in names

    row = IncomingRowData(
        path_name="impact",
        source="SRT",
        status="ACTIVE",
        bitrate_receive_mbps=5.0,
        health_status=HealthStatus.HEALTHY,
    )

    assert row.transport_source_id is None


def test_source_replacement_projects_new_identity():
    from dataclasses import replace

    original = make_path()

    first = replace(
        original,
        source=MediaSource(
            source_type="srtConn",
            source_id="publisher-A",
        ),
    )

    second = replace(
        original,
        source=MediaSource(
            source_type="srtConn",
            source_id="publisher-B",
        ),
    )

    first_row = build_panel(media_path=first).rows[0]
    second_row = build_panel(media_path=second).rows[0]

    assert first_row.path_name == second_row.path_name
    assert first_row.transport_source_type == second_row.transport_source_type

    assert first_row.transport_source_id == "publisher-A"
    assert second_row.transport_source_id == "publisher-B"
    assert first_row.transport_source_id != second_row.transport_source_id
