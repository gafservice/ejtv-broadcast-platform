"""Rolling bitrate statistics for INCOMING transport paths.

This component is intentionally independent of MediaMTX,
StreamingService and the dashboard renderer.

Statistics are held in memory and are scoped by path.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite


@dataclass(frozen=True)
class IncomingTransportBitrateStatistics:
    average_mbps: float | None = None
    minimum_mbps: float | None = None
    maximum_mbps: float | None = None


class IncomingTransportBitrateWindow:
    """Maintain rolling bitrate samples independently per path."""

    def __init__(self, window_seconds: int = 60) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        self._window = timedelta(seconds=window_seconds)
        self._samples: dict[
            str, deque[tuple[datetime, float]]
        ] = {}

        self._last_observed_at: dict[str, datetime] = {}

    @staticmethod
    def _validate_timestamp(observed_at: datetime) -> None:
        if (
            observed_at.tzinfo is None
            or observed_at.utcoffset() is None
        ):
            raise ValueError(
                "observed_at must be timezone-aware"
            )

    def _expire(
        self,
        path: str,
        observed_at: datetime,
    ) -> None:
        samples = self._samples.get(path)

        if not samples:
            return

        cutoff = observed_at - self._window

        while samples and samples[0][0] < cutoff:
            samples.popleft()

        if not samples:
            self._samples.pop(path, None)

    def observe(
        self,
        path: str,
        *,
        observed_at: datetime,
        bitrate_mbps: float | None,
    ) -> None:
        """Add a valid sample and expire older samples.

        None represents an unavailable measurement.
        """

        self._validate_timestamp(observed_at)

        if bitrate_mbps is not None:
            if (
                not isfinite(bitrate_mbps)
                or bitrate_mbps < 0
            ):
                raise ValueError(
                    "bitrate_mbps must be finite and non-negative"
                )

        last_observed_at = self._last_observed_at.get(path)

        if (
            last_observed_at is not None
            and observed_at < last_observed_at
        ):
            raise ValueError(
                "Out-of-order bitrate observation"
            )

        self._last_observed_at[path] = observed_at

        self._expire(path, observed_at)

        if bitrate_mbps is None:
            return

        samples = self._samples.setdefault(path, deque())

        samples.append(
            (observed_at, float(bitrate_mbps))
        )

    def reset(self, path: str) -> None:
        """Discard bitrate history and timestamp for one path.

        Other paths remain unchanged.
        """

        self._samples.pop(path, None)
        self._last_observed_at.pop(path, None)

    def reconcile_paths(
        self,
        path_names: tuple[str, ...],
    ) -> None:
        """Discard history for paths absent from a valid inventory.

        The caller is responsible for providing a complete,
        trustworthy inventory. This method does not determine
        whether a MediaMTX capture is complete or valid.
        """

        if not isinstance(path_names, tuple):
            raise TypeError("path_names must be a tuple")

        if any(
            not isinstance(path, str) or not path
            for path in path_names
        ):
            raise ValueError(
                "path_names must contain non-empty strings"
            )

        if len(path_names) != len(set(path_names)):
            raise ValueError(
                "path_names must not contain duplicates"
            )

        known_paths = set(path_names)

        tracked_paths = (
            set(self._samples)
            | set(self._last_observed_at)
        )

        for path in tracked_paths - known_paths:
            self.reset(path)

    def get(
        self,
        path: str,
        *,
        observed_at: datetime,
    ) -> IncomingTransportBitrateStatistics:
        """Return statistics for samples inside the time window."""

        self._validate_timestamp(observed_at)

        last_observed_at = self._last_observed_at.get(path)

        if (
            last_observed_at is not None
            and observed_at < last_observed_at
        ):
            raise ValueError(
                "Out-of-order statistics query"
            )

        self._expire(path, observed_at)

        samples = self._samples.get(path)

        if not samples:
            return IncomingTransportBitrateStatistics()

        values = [bitrate for _, bitrate in samples]

        return IncomingTransportBitrateStatistics(
            average_mbps=sum(values) / len(values),
            minimum_mbps=min(values),
            maximum_mbps=max(values),
        )
