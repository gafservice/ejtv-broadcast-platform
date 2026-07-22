#!/usr/bin/env python3

from datetime import datetime, timezone

from rich.console import Console

from app.dashboard.models import ServerPanelData
from app.dashboard.renderers.server_panel_renderer import (
    ServerPanelRenderer,
)

console = Console()

data = ServerPanelData(
    hostname="ejtv-01",
    mediamtx_online=True,
    api_online=True,
    snapshot_at=datetime.now(timezone.utc),
    quality="AVAILABLE",
)

panel = ServerPanelRenderer().render(data)

console.print(panel)