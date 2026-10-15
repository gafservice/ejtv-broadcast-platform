"""Immutable state for INCOMING contextual detail tabs."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


class IncomingDetailTab(str, Enum):
    """Available contextual tabs within TerminalView.INCOMING."""

    SIGNAL = "signal"
    TRANSPORT = "transport"
    VIDEO = "video"
    AUDIO = "audio"
    EVENTS = "events"
    STATISTICS = "statistics"


@dataclass(frozen=True)
class IncomingDetailTabState:
    """Immutable selection of the active INCOMING detail tab."""

    active_tab: IncomingDetailTab = IncomingDetailTab.SIGNAL

    def __post_init__(self) -> None:
        if not isinstance(self.active_tab, IncomingDetailTab):
            raise TypeError(
                "active_tab must be an IncomingDetailTab"
            )

    def select(
        self,
        tab: IncomingDetailTab,
    ) -> "IncomingDetailTabState":
        """Return a new state with the requested active tab."""

        if not isinstance(tab, IncomingDetailTab):
            raise TypeError(
                "tab must be an IncomingDetailTab"
            )

        return replace(self, active_tab=tab)
