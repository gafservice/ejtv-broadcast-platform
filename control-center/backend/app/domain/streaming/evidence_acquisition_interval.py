"""Protocol-independent acquisition interval for transport evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class EvidenceAcquisitionInterval:
    """UTC interval during which external evidence was acquired.

    This interval describes acquisition timing, not the internal
    measurement window of the evidence source.
    """

    started_at: datetime
    completed_at: datetime
    source: str

    def __post_init__(self) -> None:
        for field_name in ("started_at", "completed_at"):
            value = getattr(self, field_name)

            if not isinstance(value, datetime):
                raise ValueError(
                    f"{field_name} must be a datetime"
                )

            if (
                value.tzinfo is None
                or value.utcoffset() != timedelta(0)
            ):
                raise ValueError(
                    f"{field_name} must use UTC"
                )

        if self.completed_at < self.started_at:
            raise ValueError(
                "completed_at must not precede started_at"
            )

        if (
            not isinstance(self.source, str)
            or not self.source.strip()
        ):
            raise ValueError(
                "source must be a non-empty string"
            )

    @property
    def duration_seconds(self) -> float:
        """Return elapsed wall-clock time in seconds."""

        return (
            self.completed_at - self.started_at
        ).total_seconds()
