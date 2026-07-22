"""Demostración visual del dashboard completo."""

from datetime import datetime, timezone

from rich.console import Console

from app.dashboard.models import (
    DashboardData,
    PathRowData,
    ServerPanelData,
    StreamingPanelData,
)
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer


def main() -> None:
    """Renderiza un dashboard de ejemplo en la terminal."""

    data = DashboardData(
        server=ServerPanelData(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot_at=datetime.now(timezone.utc),
            quality="AVAILABLE",
        ),
        streaming=StreamingPanelData(
            active_paths=3,
            readers=8,
            inbound_bitrate_bps=18_000_000,
            outbound_bitrate_bps=52_000_000,
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
            PathRowData(
                name="canal-2",
                source="SRT",
                readers=3,
                inbound_bitrate_bps=6_000_000,
                outbound_bitrate_bps=12_000_000,
                status="ACTIVE",
                quality="AVAILABLE",
            ),
            PathRowData(
                name="canal-3",
                source="RTMP",
                readers=0,
                inbound_bitrate_bps=4_000_000,
                outbound_bitrate_bps=0,
                status="IDLE",
                quality="AVAILABLE",
            ),
        ),
    )

    renderer = DashboardRenderer()
    layout = renderer.render(data)

    console = Console()
    console.print(layout)


if __name__ == "__main__":
    main()
