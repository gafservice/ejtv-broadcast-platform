"""Pruebas para DashboardRenderer."""
from rich.console import Console

from app.domain.streaming import HealthStatus, StreamingHealth

from datetime import datetime, timezone

from rich.layout import Layout

from app.dashboard.models import (
    DashboardData,
    PathRowData,
    ServerPanelData,
    SessionPanelData,
    StreamingPanelData,
)
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer


def build_dashboard_data() -> DashboardData:
    """Construye datos válidos para las pruebas del renderer."""

    return DashboardData(
        server=ServerPanelData(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot_at=datetime(
                2026,
                7,
                21,
                14,
                0,
                tzinfo=timezone.utc,
            ),
            quality="AVAILABLE",
        ),
        streaming=StreamingPanelData(
            active_paths=1,
            readers=5,
            inbound_bitrate_bps=8_000_000,
            outbound_bitrate_bps=40_000_000,
            quality="AVAILABLE",
        ),
        paths=(
            PathRowData(
                name="enlace",
                source="UDP",
                readers=5,
                inbound_bitrate_bps=8_000_000,
                outbound_bitrate_bps=40_000_000,
                status="ACTIVE",
                quality="AVAILABLE",
            ),
        ),
        health=None,
    )


def test_dashboard_renderer_can_be_created() -> None:
    renderer = DashboardRenderer()

    assert renderer is not None


def test_render_returns_rich_layout() -> None:
    renderer = DashboardRenderer()
    data = build_dashboard_data()

    layout = renderer.render(data)

    assert isinstance(layout, Layout)
def test_render_contains_health_panel() -> None:
    renderer = DashboardRenderer()
    data = build_dashboard_data()

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=160,
        color_system=None,
    )
    console.print(layout)

    output = console.export_text()

    assert "STREAM HEALTH" in output
    assert "UNKNOWN" in output
    assert "No health data available." in output


def test_render_contains_streaming_health_data() -> None:
    renderer = DashboardRenderer()
    data = build_dashboard_data()

    health = StreamingHealth(
        captured_at=data.server.snapshot_at,
        paths=(),
        status=HealthStatus.HEALTHY,
        message="El subsistema SRT funciona correctamente.",
    )

    data = DashboardData(
        server=data.server,
        streaming=data.streaming,
        paths=data.paths,
        health=health,
    )

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=160,
        color_system=None,
    )
    console.print(layout)

    output = console.export_text()

    assert "STREAM HEALTH" in output
    assert "HEALTHY" in output
    assert "Summary" in output
    assert "El subsistema SRT funciona" in output
    assert "…" in output


def test_render_contains_active_clients_panel() -> None:
    """Debe renderizar ACTIVE CLIENTS cuando hay datos de sesiones."""

    renderer = DashboardRenderer()
    base_data = build_dashboard_data()

    data = DashboardData(
        server=base_data.server,
        streaming=base_data.streaming,
        paths=base_data.paths,
        sessions=SessionPanelData(
            total_sessions=6,
            readers=5,
            publishers=1,
            degraded_sessions=1,
            critical_sessions=0,
            inbound_bitrate_bps=8_000_000,
            outbound_bitrate_bps=40_000_000,
            quality="GOOD",
            protocol_counts=(
                ("SRT", 3),
                ("RTMP", 1),
                ("RTSP", 1),
                ("HLS", 1),
                ("WebRTC", 0),
                ("UNKNOWN", 0),
            ),
        ),
        health=base_data.health,
    )

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=160,
        color_system=None,
    )
    console.print(layout)

    output = console.export_text()

    assert "ACTIVE CLIENTS" in output

    assert "SRT" in output
    assert "RTMP" in output
    assert "RTSP" in output
    assert "HLS" in output
    assert "WebRTC" in output

    assert "TOTAL" in output

    assert "Inbound" in output
    assert "Outbound" in output
    assert "GOOD" not in output

    assert "Sessions" not in output
    assert "Publishers" not in output
    assert "Degraded" not in output
    assert "Critical" not in output

def test_render_contains_network_interfaces_panel() -> None:
    from app.dashboard.models import (
        NetworkInterfaceRowData,
        NetworkInterfacesPanelData,
    )

    renderer = DashboardRenderer()
    base_data = build_dashboard_data()

    network_interfaces = NetworkInterfacesPanelData(
        interfaces=(
            NetworkInterfaceRowData(
                interface="enp9s0",
                interface_type="ETHERNET",
                is_up=True,
                carrier=True,
                link_speed_mbps=1000,
                mtu=1500,
                mac_address="3c:07:54:7c:b5:88",
                ipv4_addresses=("10.0.18.54",),
                ipv6_addresses=(),
                rx_bps=9_000_000.0,
                tx_bps=418.0,
                errors_in=0,
                errors_out=0,
                dropped_in=0,
                dropped_out=0,
                dropped_in_per_second=0.0,
            ),
            NetworkInterfaceRowData(
                interface="ens2f1",
                interface_type="ETHERNET",
                is_up=False,
                carrier=False,
                link_speed_mbps=None,
                mtu=1500,
                mac_address="00:e0:ed:2c:6d:c1",
                ipv4_addresses=(),
                ipv6_addresses=(),
                rx_bps=0.0,
                tx_bps=0.0,
                errors_in=0,
                errors_out=0,
                dropped_in=0,
                dropped_out=0,
                dropped_in_per_second=0.0,
            ),
        ),
        captured_at=base_data.server.snapshot_at,
    )

    data = DashboardData(
        server=base_data.server,
        streaming=base_data.streaming,
        paths=base_data.paths,
        health=base_data.health,
        network_interfaces=network_interfaces,
    )

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=160,
        height=60,
        color_system=None,
    )

    console.print(layout)

    output = console.export_text()

    assert "NETWORK INTERFACES" in output
    assert "enp9s0" in output
    assert "ens2f1" in output
    assert "1 Gbps" in output
    assert "9.00 Mbps" in output
    assert "DOWN" in output


def test_render_preserves_legacy_layout_without_network_interfaces() -> None:
    renderer = DashboardRenderer()
    data = build_dashboard_data()

    layout = renderer.render(data)

    assert data.network_interfaces is None

    console = Console(
        record=True,
        width=160,
        height=60,
        color_system=None,
    )

    console.print(layout)

    output = console.export_text()

    assert "NETWORK INTERFACES" not in output


def test_render_contains_node_health_panel() -> None:
    from datetime import UTC, datetime

    from app.dashboard.models import (
        NodeHealthPanelData,
    )

    renderer = DashboardRenderer()
    base_data = build_dashboard_data()

    node_health = NodeHealthPanelData(
        state="HEALTHY",
        system_state="HEALTHY",
        network_state="HEALTHY",
        interfaces=(),
        captured_at=datetime(
            2026,
            8,
            18,
            23,
            59,
            tzinfo=UTC,
        ),
    )

    data = DashboardData(
        server=base_data.server,
        streaming=base_data.streaming,
        paths=base_data.paths,
        health=base_data.health,
        system=base_data.system,
        sessions=base_data.sessions,
        active_connections=base_data.active_connections,
        network_interfaces=base_data.network_interfaces,
        node_health=node_health,
    )

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=180,
        color_system=None,
    )

    console.print(layout)

    output = console.export_text()

    assert "NODE HEALTH" in output
    assert "Status: HEALTHY" in output
    assert "System: HEALTHY" in output
    assert "Network: HEALTHY" in output


def test_render_contains_recent_events_panel() -> None:
    from datetime import UTC, datetime

    from app.dashboard.models import (
        RecentEventRowData,
        RecentEventsPanelData,
    )

    renderer = DashboardRenderer()
    base_data = build_dashboard_data()

    recent_events = RecentEventsPanelData(
        events=(
            RecentEventRowData(
                event_id="event-001",
                event_type="NODE_HEALTH_DEGRADED",
                severity="WARNING",
                title="Node health degraded",
                occurred_at=datetime(
                    2026,
                    8,
                    20,
                    18,
                    30,
                    15,
                    tzinfo=UTC,
                ),
            ),
            RecentEventRowData(
                event_id="event-002",
                event_type="NODE_HEALTH_RECOVERED",
                severity="INFO",
                title="Node health recovered",
                occurred_at=datetime(
                    2026,
                    8,
                    20,
                    18,
                    32,
                    10,
                    tzinfo=UTC,
                ),
            ),
        ),
    )

    data = DashboardData(
        server=base_data.server,
        streaming=base_data.streaming,
        paths=base_data.paths,
        health=base_data.health,
        system=base_data.system,
        sessions=base_data.sessions,
        active_connections=base_data.active_connections,
        network_interfaces=base_data.network_interfaces,
        node_health=base_data.node_health,
        recent_events=recent_events,
    )

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=180,
        height=70,
        color_system=None,
    )

    console.print(layout)

    output = console.export_text()

    assert "RECENT EVENTS" in output
    assert "NODE_HEALTH_DEGRADED" in output
    assert "NODE_HEALTH_RECOVERED" in output
    assert "Node health degraded" in output
    assert "Node health recovered" in output


def test_render_preserves_layout_without_recent_events() -> None:
    renderer = DashboardRenderer()
    data = build_dashboard_data()

    assert data.recent_events is None

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=180,
        height=60,
        color_system=None,
    )

    console.print(layout)

    output = console.export_text()

    assert "RECENT EVENTS" not in output


def test_render_contains_active_alarms_panel() -> None:
    from datetime import UTC, datetime

    from app.dashboard.models import (
        ActiveAlarmRowData,
        ActiveAlarmsPanelData,
    )

    renderer = DashboardRenderer()
    base_data = build_dashboard_data()

    active_alarms = ActiveAlarmsPanelData(
        alarms=(
            ActiveAlarmRowData(
                alarm_id="alarm-001",
                alarm_type="NODE_HEALTH_DEGRADED",
                severity="CRITICAL",
                state="ACTIVE",
                message="Node health degraded to CRITICAL",
                opened_at=datetime(
                    2026,
                    8,
                    21,
                    23,
                    30,
                    15,
                    tzinfo=UTC,
                ),
            ),
            ActiveAlarmRowData(
                alarm_id="alarm-002",
                alarm_type="NODE_HEALTH_DEGRADED",
                severity="WARNING",
                state="ACKNOWLEDGED",
                message="Node health degraded to WARNING",
                opened_at=datetime(
                    2026,
                    8,
                    21,
                    23,
                    31,
                    10,
                    tzinfo=UTC,
                ),
            ),
        ),
    )

    data = DashboardData(
        server=base_data.server,
        streaming=base_data.streaming,
        paths=base_data.paths,
        health=base_data.health,
        system=base_data.system,
        sessions=base_data.sessions,
        active_connections=base_data.active_connections,
        network_interfaces=base_data.network_interfaces,
        node_health=base_data.node_health,
        recent_events=base_data.recent_events,
        active_alarms=active_alarms,
    )

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=180,
        height=80,
        color_system=None,
    )

    console.print(layout)

    output = console.export_text()

    assert "ACTIVE ALARMS" in output
    assert "NODE_HEALTH_DEGRADED" in output
    assert "CRITICAL" in output
    assert "WARNING" in output
    assert "ACTIVE" in output
    assert "ACKNOWLEDGED" in output
    assert "Node health degraded to CRITICAL" in output


def test_render_preserves_layout_without_active_alarms() -> None:
    renderer = DashboardRenderer()
    data = build_dashboard_data()

    assert data.active_alarms is None

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=180,
        height=60,
        color_system=None,
    )

    console.print(layout)

    output = console.export_text()

    assert "ACTIVE ALARMS" not in output


def test_active_alarms_precede_recent_events_in_layout() -> None:
    from datetime import UTC, datetime

    from app.dashboard.models import (
        ActiveAlarmRowData,
        ActiveAlarmsPanelData,
        RecentEventRowData,
        RecentEventsPanelData,
    )

    renderer = DashboardRenderer()
    base_data = build_dashboard_data()

    active_alarms = ActiveAlarmsPanelData(
        alarms=(
            ActiveAlarmRowData(
                alarm_id="alarm-001",
                alarm_type="NODE_HEALTH_DEGRADED",
                severity="CRITICAL",
                state="ACTIVE",
                message="Critical health alarm",
                opened_at=datetime(
                    2026,
                    8,
                    21,
                    23,
                    30,
                    tzinfo=UTC,
                ),
            ),
        ),
    )

    recent_events = RecentEventsPanelData(
        events=(
            RecentEventRowData(
                event_id="event-001",
                event_type="NODE_HEALTH_DEGRADED",
                severity="CRITICAL",
                title="Node health degraded",
                occurred_at=datetime(
                    2026,
                    8,
                    21,
                    23,
                    30,
                    tzinfo=UTC,
                ),
            ),
        ),
    )

    data = DashboardData(
        server=base_data.server,
        streaming=base_data.streaming,
        paths=base_data.paths,
        health=base_data.health,
        active_alarms=active_alarms,
        recent_events=recent_events,
    )

    layout = renderer.render(data)

    child_names = [
        child.name
        for child in layout.children
    ]

    assert "active_alarms" in child_names
    assert "recent_events" in child_names

    assert (
        child_names.index("active_alarms")
        < child_names.index("recent_events")
    )


def test_navigation_visual_state_decorates_navigable_panels() -> None:
    """Los paneles navegables deben mostrar foco y posición."""

    from datetime import UTC, datetime

    from app.dashboard.models import (
        ActiveAlarmsPanelData,
        ActiveConnectionsPanelData,
        RecentEventsPanelData,
    )
    from app.dashboard.models.dashboard_navigation_state import (
        DashboardNavigationState,
        NavigablePanel,
    )

    renderer = DashboardRenderer()
    base_data = build_dashboard_data()

    data = DashboardData(
        server=base_data.server,
        streaming=base_data.streaming,
        paths=base_data.paths,
        health=base_data.health,
        active_connections=ActiveConnectionsPanelData(
            captured_at=datetime(
                2026,
                9,
                1,
                12,
                0,
                tzinfo=UTC,
            ),
            connections=(),
            total_items=0,
        ),
        active_alarms=ActiveAlarmsPanelData(
            alarms=(),
            total_items=0,
        ),
        recent_events=RecentEventsPanelData(
            events=(),
            total_items=0,
        ),
    )

    navigation_state = DashboardNavigationState(
        active_panel=NavigablePanel.ACTIVE_CONNECTIONS,
    )

    layout = renderer.render(
        data,
        navigation_state=navigation_state,
    )

    connections_panel = (
        layout["active_connections"].renderable
    )
    alarms_panel = (
        layout["active_alarms"].renderable
    )
    events_panel = (
        layout["recent_events"].renderable
    )

    assert "0 / 0" in str(connections_panel.title)
    assert "0 / 0" in str(alarms_panel.title)
    assert "0 / 0" in str(events_panel.title)

    assert connections_panel.border_style == "bold bright_yellow"
    assert alarms_panel.border_style != "bold bright_yellow"
    assert events_panel.border_style != "bold bright_yellow"


def test_navigation_visual_focus_follows_active_panel() -> None:
    """El foco visual debe seguir al panel seleccionado."""

    from datetime import UTC, datetime

    from app.dashboard.models import (
        ActiveAlarmsPanelData,
        ActiveConnectionsPanelData,
        RecentEventsPanelData,
    )
    from app.dashboard.models.dashboard_navigation_state import (
        DashboardNavigationState,
        NavigablePanel,
    )

    renderer = DashboardRenderer()
    base_data = build_dashboard_data()

    data = DashboardData(
        server=base_data.server,
        streaming=base_data.streaming,
        paths=base_data.paths,
        health=base_data.health,
        active_connections=ActiveConnectionsPanelData(
            captured_at=datetime(
                2026,
                9,
                1,
                12,
                0,
                tzinfo=UTC,
            ),
            connections=(),
            total_items=0,
        ),
        active_alarms=ActiveAlarmsPanelData(
            alarms=(),
            total_items=0,
        ),
        recent_events=RecentEventsPanelData(
            events=(),
            total_items=0,
        ),
    )

    navigation_state = DashboardNavigationState(
        active_panel=NavigablePanel.ACTIVE_ALARMS,
    )

    layout = renderer.render(
        data,
        navigation_state=navigation_state,
    )

    assert (
        layout["active_connections"]
        .renderable
        .border_style
        != "bold bright_yellow"
    )

    assert (
        layout["active_alarms"]
        .renderable
        .border_style
        == "bold bright_yellow"
    )

    assert (
        layout["recent_events"]
        .renderable
        .border_style
        != "bold bright_yellow"
    )


def test_navigation_visual_position_uses_viewport_bounds() -> None:
    """El título debe indicar la ventana visible dentro del total."""

    from app.dashboard.models import (
        RecentEventsPanelData,
    )
    from app.dashboard.models.dashboard_navigation_state import (
        DashboardNavigationState,
        NavigablePanel,
    )
    from app.dashboard.models.panel_viewport import (
        PanelViewport,
    )

    renderer = DashboardRenderer()
    base_data = build_dashboard_data()

    data = DashboardData(
        server=base_data.server,
        streaming=base_data.streaming,
        paths=base_data.paths,
        health=base_data.health,
        recent_events=RecentEventsPanelData(
            events=(),
            total_items=27,
        ),
    )

    navigation_state = DashboardNavigationState(
        active_panel=NavigablePanel.RECENT_EVENTS,
        recent_events=PanelViewport(
            offset=5,
            page_size=5,
        ),
    )

    layout = renderer.render(
        data,
        navigation_state=navigation_state,
    )

    panel = layout["recent_events"].renderable

    assert "6–10 / 27" in str(panel.title)
    assert panel.border_style == "bold bright_yellow"
