"""Pure vertical geometry policy for INCOMING V2."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IncomingVerticalGeometry:
    """Calculated terminal allocation for the INCOMING view."""

    header_height: int
    list_height: int
    detail_height: int
    visible_rows: int
    insufficient_height: bool


class IncomingVerticalGeometryPolicy:
    """Calculate vertical allocation without changing dashboard state."""

    HEADER_HEIGHT = 3
    LIST_OVERHEAD = 3
    MINIMUM_LIST_HEIGHT = 3
    MINIMUM_DETAIL_HEIGHT = 12
    COMPACT_DETAIL_HEIGHT = 8

    def calculate(
        self,
        *,
        terminal_height: int,
        signal_count: int,
        maximum_visible_rows: int,
    ) -> IncomingVerticalGeometry:
        """Return a bounded vertical allocation for INCOMING."""

        values = {
            "terminal_height": terminal_height,
            "signal_count": signal_count,
            "maximum_visible_rows": maximum_visible_rows,
        }

        for name, value in values.items():
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")

        if terminal_height <= 0:
            raise ValueError("terminal_height must be positive")

        if signal_count < 0:
            raise ValueError("signal_count must not be negative")

        if maximum_visible_rows <= 0:
            raise ValueError(
                "maximum_visible_rows must be positive"
            )

        header_height = min(
            self.HEADER_HEIGHT,
            terminal_height,
        )

        available_height = max(
            0,
            terminal_height - header_height,
        )

        requested_rows = min(
            signal_count,
            maximum_visible_rows,
        )

        requested_list_height = max(
            self.MINIMUM_LIST_HEIGHT,
            requested_rows + self.LIST_OVERHEAD,
        )

        insufficient_height = (
            available_height
            < self.MINIMUM_LIST_HEIGHT
            + self.MINIMUM_DETAIL_HEIGHT
        )

        reserved_detail_height = min(
            available_height,
            (
                self.COMPACT_DETAIL_HEIGHT
                if insufficient_height
                else self.MINIMUM_DETAIL_HEIGHT
            ),
        )

        maximum_list_height = max(
            0,
            available_height - reserved_detail_height,
        )

        list_height = min(
            requested_list_height,
            maximum_list_height,
        )

        visible_rows = min(
            requested_rows,
            max(
                0,
                list_height - self.LIST_OVERHEAD,
            ),
        )

        detail_height = max(
            0,
            available_height - list_height,
        )

        return IncomingVerticalGeometry(
            header_height=header_height,
            list_height=list_height,
            detail_height=detail_height,
            visible_rows=visible_rows,
            insufficient_height=insufficient_height,
        )
