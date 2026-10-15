"""Adaptive visual tab strip for INCOMING signal details."""

from __future__ import annotations

from rich.text import Text

from app.dashboard.models.incoming_detail_tab_state import (
    IncomingDetailTab,
)


class IncomingDetailTabStrip:
    """Render six contextual tabs without changing signal state."""

    _TABS = (
        IncomingDetailTab.SIGNAL,
        IncomingDetailTab.TRANSPORT,
        IncomingDetailTab.VIDEO,
        IncomingDetailTab.AUDIO,
        IncomingDetailTab.EVENTS,
        IncomingDetailTab.STATISTICS,
    )

    _FULL_LABELS = (
        "SIGNAL",
        "TRANSPORT",
        "VIDEO",
        "AUDIO",
        "EVENTS",
        "STATS",
    )

    _COMPACT_LABELS = (
        "SIG",
        "TRN",
        "VID",
        "AUD",
        "EVT",
        "STA",
    )

    @classmethod
    def render(
        cls,
        *,
        active_tab: IncomingDetailTab,
        width: int,
    ) -> Text:
        """Build a width-bounded Rich Text navigation strip."""

        if not isinstance(active_tab, IncomingDetailTab):
            raise TypeError(
                "active_tab must be an IncomingDetailTab"
            )

        if not isinstance(width, int) or width <= 0:
            raise ValueError(
                "width must be a positive integer"
            )

        full = tuple(
            f"{index} {label}"
            for index, label in enumerate(
                cls._FULL_LABELS,
                start=1,
            )
        )

        compact = tuple(
            f"{index} {label}"
            for index, label in enumerate(
                cls._COMPACT_LABELS,
                start=1,
            )
        )

        numbers = tuple(
            str(index)
            for index in range(1, 7)
        )

        separator = " | "

        def required_width(labels):
            return len(separator.join(labels))

        if required_width(full) <= width:
            labels = full
        elif required_width(compact) <= width:
            labels = compact
        else:
            labels = numbers
            separator = "  "

        result = Text(
            no_wrap=True,
            overflow="crop",
        )

        for index, (tab, label) in enumerate(
            zip(cls._TABS, labels)
        ):
            if index:
                result.append(separator)

            style = (
                "bold reverse"
                if tab is active_tab
                else "dim"
            )

            result.append(
                label,
                style=style,
            )

        return result
