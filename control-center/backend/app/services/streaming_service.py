"""Servicios de aplicación para mediciones multimedia derivadas."""

from __future__ import annotations

from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    MediaPath,
    StreamingMeasurement,
    StreamingPathMeasurement,
)


class StreamingService:
    """Compara snapshots multimedia y genera mediciones derivadas."""

    def compare(
        self,
        previous: MediaMTXSnapshot | None,
        current: MediaMTXSnapshot,
    ) -> StreamingMeasurement:
        """Genera una medición a partir del estado actual y el anterior."""

        if previous is None:
            return self._build_initial_measurement(current)

        interval_seconds = (
            current.captured_at - previous.captured_at
        ).total_seconds()

        if interval_seconds <= 0:
            return self._build_invalid_measurement(
                previous=previous,
                current=current,
            )

        previous_paths = {
            path.name: path
            for path in previous.paths
        }

        path_measurements = tuple(
            self._compare_path(
                previous=previous_paths.get(current_path.name),
                current=current_path,
                interval_seconds=interval_seconds,
            )
            for current_path in current.paths
        )

        quality = self._resolve_global_quality(path_measurements)

        if quality is MeasurementQuality.AVAILABLE:
            total_inbound_bitrate_bps = sum(
                path.inbound_bitrate_bps or 0.0
                for path in path_measurements
            )
            total_outbound_bitrate_bps = sum(
                path.outbound_bitrate_bps or 0.0
                for path in path_measurements
            )
        else:
            total_inbound_bitrate_bps = None
            total_outbound_bitrate_bps = None

        return StreamingMeasurement(
            captured_at=current.captured_at,
            previous_captured_at=previous.captured_at,
            interval_seconds=interval_seconds,
            paths=path_measurements,
            total_inbound_bitrate_bps=total_inbound_bitrate_bps,
            total_outbound_bitrate_bps=total_outbound_bitrate_bps,
            quality=quality,
        )

    def _build_initial_measurement(
        self,
        current: MediaMTXSnapshot,
    ) -> StreamingMeasurement:
        """Construye la medición inicial cuando no existe historial."""

        paths = tuple(
            self._build_unavailable_path(
                current=path,
                previous=None,
            )
            for path in current.paths
        )

        return StreamingMeasurement(
            captured_at=current.captured_at,
            previous_captured_at=None,
            interval_seconds=None,
            paths=paths,
            total_inbound_bitrate_bps=None,
            total_outbound_bitrate_bps=None,
            quality=MeasurementQuality.NOT_AVAILABLE,
        )

    def _build_invalid_measurement(
        self,
        *,
        previous: MediaMTXSnapshot,
        current: MediaMTXSnapshot,
    ) -> StreamingMeasurement:
        """Construye una medición inválida por inconsistencia temporal."""

        previous_paths = {
            path.name: path
            for path in previous.paths
        }

        paths = tuple(
            self._build_invalid_path(
                current=current_path,
                previous=previous_paths.get(current_path.name),
            )
            for current_path in current.paths
        )

        return StreamingMeasurement(
            captured_at=current.captured_at,
            previous_captured_at=previous.captured_at,
            interval_seconds=None,
            paths=paths,
            total_inbound_bitrate_bps=None,
            total_outbound_bitrate_bps=None,
            quality=MeasurementQuality.INVALID,
        )

    def _compare_path(
        self,
        *,
        previous: MediaPath | None,
        current: MediaPath,
        interval_seconds: float,
    ) -> StreamingPathMeasurement:
        """Compara el estado de un path entre dos snapshots."""

        if previous is None:
            return self._build_unavailable_path(
                current=current,
                previous=None,
            )

        inbound_delta = current.inbound_bytes - previous.inbound_bytes
        outbound_delta = current.outbound_bytes - previous.outbound_bytes

        if inbound_delta < 0 or outbound_delta < 0:
            return self._build_invalid_path(
                current=current,
                previous=previous,
            )

        reader_delta = current.reader_count - previous.reader_count

        return StreamingPathMeasurement(
            name=current.name,
            status=current.status,
            previous_status=previous.status,
            reader_count=current.reader_count,
            reader_delta=reader_delta,
            inbound_delta_bytes=inbound_delta,
            outbound_delta_bytes=outbound_delta,
            inbound_bitrate_bps=self._calculate_bitrate(
                byte_delta=inbound_delta,
                interval_seconds=interval_seconds,
            ),
            outbound_bitrate_bps=self._calculate_bitrate(
                byte_delta=outbound_delta,
                interval_seconds=interval_seconds,
            ),
            state_changed=current.status is not previous.status,
            quality=MeasurementQuality.AVAILABLE,
        )

    @staticmethod
    def _calculate_bitrate(
        *,
        byte_delta: int,
        interval_seconds: float,
    ) -> float:
        """Calcula bits por segundo durante un intervalo válido."""

        return byte_delta * 8 / interval_seconds

    @staticmethod
    def _build_unavailable_path(
        *,
        current: MediaPath,
        previous: MediaPath | None,
    ) -> StreamingPathMeasurement:
        """Construye una medición sin información histórica suficiente."""

        return StreamingPathMeasurement(
            name=current.name,
            status=current.status,
            previous_status=(
                previous.status
                if previous is not None
                else None
            ),
            reader_count=current.reader_count,
            reader_delta=None,
            inbound_delta_bytes=None,
            outbound_delta_bytes=None,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            state_changed=(
                previous is not None
                and current.status is not previous.status
            ),
            quality=MeasurementQuality.NOT_AVAILABLE,
        )

    @staticmethod
    def _build_invalid_path(
        *,
        current: MediaPath,
        previous: MediaPath | None,
    ) -> StreamingPathMeasurement:
        """Construye una medición que no debe considerarse confiable."""

        return StreamingPathMeasurement(
            name=current.name,
            status=current.status,
            previous_status=(
                previous.status
                if previous is not None
                else None
            ),
            reader_count=current.reader_count,
            reader_delta=None,
            inbound_delta_bytes=None,
            outbound_delta_bytes=None,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            state_changed=(
                previous is not None
                and current.status is not previous.status
            ),
            quality=MeasurementQuality.INVALID,
        )

    @staticmethod
    def _resolve_global_quality(
        paths: tuple[StreamingPathMeasurement, ...],
    ) -> MeasurementQuality:
        """Determina la calidad general de la medición."""

        if any(
            path.quality is MeasurementQuality.INVALID
            for path in paths
        ):
            return MeasurementQuality.INVALID

        if any(
            path.quality is MeasurementQuality.NOT_AVAILABLE
            for path in paths
        ):
            return MeasurementQuality.NOT_AVAILABLE

        return MeasurementQuality.AVAILABLE
