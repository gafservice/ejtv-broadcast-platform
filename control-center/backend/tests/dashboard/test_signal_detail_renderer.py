"""Contract tests for contextual INCOMING Signal Detail."""

from rich.console import Console

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.renderers.signal_detail_renderer import (
    SignalDetailRenderer,
)
from app.domain.streaming.health import HealthStatus


def test_signal_detail_projects_only_selected_path():
    data = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="ejtv",
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=4.0,
                health_status=HealthStatus.HEALTHY,
                protocol="SRT",
                remote_address="192.0.2.10:9000",
            ),
            IncomingRowData(
                path_name="enlace",
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=6.0,
                health_status=HealthStatus.DEGRADED,
                protocol="SRT",
                remote_address="192.0.2.20:9000",
                health_reason="Packet loss detected",
                alarm_count=2,
                alarm_severity="MAJOR",
            ),
            IncomingRowData(
                path_name="impact",
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=5.0,
                health_status=HealthStatus.CRITICAL,
                protocol="SRT",
                remote_address="192.0.2.30:9000",
            ),
        ),
    )

    panel = SignalDetailRenderer().render(
        data,
        selected_path_name="enlace",
    )

    console = Console(
        record=True,
        width=180,
        color_system=None,
    )
    console.print(panel)
    output = console.export_text()

    assert "SIGNAL DETAIL" in output

    assert "enlace" in output
    assert "192.0.2.20:9000" in output
    assert "6.00 Mbps" in output
    assert "DEGRADED" in output
    assert "Packet loss detected" in output
    assert "2 MAJOR" in output

    assert "ejtv" not in output
    assert "impact" not in output
    assert "192.0.2.10:9000" not in output
    assert "192.0.2.30:9000" not in output



def test_signal_detail_alarm_indicator_matches_incoming():
    """Preserve canonical INCOMING alarm presentation."""

    from rich.table import Table

    cases = (
        (0, None, "—"),
        (1, None, "1"),
        (2, "MAJOR", "2 MAJOR"),
    )

    for count, severity, expected in cases:
        data = IncomingPanelData(
            rows=(
                IncomingRowData(
                    path_name="enlace",
                    source="SRT",
                    status="ACTIVE",
                    bitrate_receive_mbps=6.0,
                    health_status=HealthStatus.HEALTHY,
                    alarm_count=count,
                    alarm_severity=severity,
                ),
            ),
        )

        panel = SignalDetailRenderer().render(
            data,
            selected_path_name="enlace",
        )

        table = panel.renderable

        assert isinstance(table, Table)

        rows = tuple(
            tuple(cell for cell in row)
            for row in zip(
                *(
                    tuple(column.cells)
                    for column in table.columns
                )
            )
        )

        summary = next(
            value
            for label, value in rows
            if label == "Summary"
        )

        assert summary == expected



def test_signal_detail_invalid_selection_is_empty():
    """SD-07/SD-08: never substitute another signal."""

    row = IncomingRowData(
        path_name="ejtv",
        source="SRT",
        status="ACTIVE",
        bitrate_receive_mbps=4.0,
        health_status=HealthStatus.HEALTHY,
        protocol="SRT",
        remote_address="192.0.2.10:9000",
    )

    cases = (
        ("NONE_SELECTION", IncomingPanelData(rows=(row,)), None),
        ("UNKNOWN_SELECTION", IncomingPanelData(rows=(row,)), "unknown"),
        ("EMPTY_ROWS", IncomingPanelData(rows=()), "ejtv"),
        ("NO_DATA", None, "ejtv"),
    )

    for name, data, selected_path in cases:
        panel = SignalDetailRenderer().render(
            data,
            selected_path_name=selected_path,
        )

        console = Console(
            record=True,
            width=120,
            color_system=None,
        )
        console.print(panel)

        output = console.export_text()

        assert "SIGNAL DETAIL" in output, name
        assert "No incoming signal selected." in output, name

        assert "192.0.2.10:9000" not in output, name
        assert "4.00 Mbps" not in output, name

        assert "Identification" not in output, name
        assert "Transport" not in output, name
        assert "Reception" not in output, name



def test_signal_detail_health_since_matches_incoming():
    """Preserve canonical INCOMING timestamp presentation."""

    from datetime import datetime, timezone

    from rich.table import Table

    from app.dashboard.renderers.incoming_panel_renderer import (
        IncomingPanelRenderer,
    )

    timestamp = datetime(
        2026, 10, 14,
        12, 30, 45,
        123456,
        tzinfo=timezone.utc,
    )

    row = IncomingRowData(
        path_name="enlace",
        source="SRT",
        status="ACTIVE",
        bitrate_receive_mbps=6.0,
        health_status=HealthStatus.DEGRADED,
        health_since=timestamp,
    )

    data = IncomingPanelData(
        rows=(row,),
        reference_at=timestamp,
    )

    panel = SignalDetailRenderer().render(
        data,
        selected_path_name="enlace",
    )

    table = panel.renderable

    assert isinstance(table, Table)

    rows = tuple(
        zip(
            *(
                tuple(column.cells)
                for column in table.columns
            )
        )
    )

    detail_since = next(
        value
        for label, value in rows
        if label == "Since"
    )

    canonical_since = (
        IncomingPanelRenderer._format_health_since(
            timestamp
        )
    )

    assert detail_since == canonical_since
    assert detail_since == "2026-10-14 12:30:45"

    assert row.health_since == timestamp



def test_signal_detail_missing_values_are_explicit():
    """Missing evidence must not become invented information."""

    from rich.table import Table

    row = IncomingRowData(
        path_name="enlace",
        source="",
        status="ACTIVE",
        bitrate_receive_mbps=None,
        health_status=None,
        protocol=None,
        remote_address=None,
        health_reason=None,
        health_since=None,
        alarm_count=0,
        alarm_severity=None,
    )

    data = IncomingPanelData(rows=(row,))

    panel = SignalDetailRenderer().render(
        data,
        selected_path_name="enlace",
    )

    table = panel.renderable

    assert isinstance(table, Table)

    rows = tuple(
        zip(
            *(
                tuple(column.cells)
                for column in table.columns
            )
        )
    )

    fields = dict(rows)

    expected = {
        "Path": "enlace",
        "Source": "N/A",
        "Protocol": "N/A",
        "Remote": "N/A",
        "Status": "ACTIVE",
        "Receive": "N/A",
        "Health Status": "N/A",
        "Reason": "N/A",
        "Since": "N/A",
        "Count": "0",
        "Severity": "N/A",
        "Summary": "—",
    }

    for label, expected_value in expected.items():
        assert fields[label] == expected_value, label
