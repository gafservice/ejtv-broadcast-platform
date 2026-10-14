"""Pure presentation policy for the INCOMING signal panel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


IncomingPresentationMode = Literal["compact", "operational", "full"]


@dataclass(frozen=True, slots=True)
class IncomingPresentationConfig:
    """Presentation-only configuration for the INCOMING panel."""

    mode: IncomingPresentationMode
    page_size: int


class IncomingPresentationPolicy:
    """Calculate INCOMING presentation capacity without capturing data."""

    COMPACT_WIDTH_THRESHOLD = 100
    FULL_WIDTH_THRESHOLD = 140
    PANEL_OVERHEAD_LINES = 3

    def calculate(
        self,
        *,
        terminal_width: int,
        incoming_height: int,
    ) -> IncomingPresentationConfig:
        """Return a presentation configuration for available dimensions."""

        if terminal_width <= 0:
            raise ValueError("terminal_width must be positive")

        if incoming_height <= 0:
            raise ValueError("incoming_height must be positive")

        if terminal_width < self.COMPACT_WIDTH_THRESHOLD:
            mode: IncomingPresentationMode = "compact"
        elif terminal_width < self.FULL_WIDTH_THRESHOLD:
            mode = "operational"
        else:
            mode = "full"

        page_size = max(
            0,
            incoming_height - self.PANEL_OVERHEAD_LINES,
        )

        return IncomingPresentationConfig(
            mode=mode,
            page_size=page_size,
        )
