"""Modelos de presentación del dashboard."""

from app.domain.streaming import StreamingHealth

from app.dashboard.models.cpu_panel import CpuPanelData
from app.dashboard.models.dashboard_models import (
    DashboardData,
    PathRowData,
    ServerPanelData,
    StreamingPanelData,
)
from app.dashboard.models.disk_panel import DiskPanelData
from app.dashboard.models.memory_panel import MemoryPanelData
from app.dashboard.models.network_panel import NetworkPanelData
from app.dashboard.models.session_panel import SessionPanelData
from app.dashboard.models.system_panel import SystemPanelData
from app.dashboard.models.uptime_panel import UptimePanelData

__all__ = [
    "CpuPanelData",
    "DashboardData",
    "DiskPanelData",
    "MemoryPanelData",
    "NetworkPanelData",
    "PathRowData",
    "ServerPanelData",
    "SessionPanelData",
    "StreamingHealth",
    "StreamingPanelData",
    "SystemPanelData",
    "UptimePanelData",
]
