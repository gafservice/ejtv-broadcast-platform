"""Operational composition for one Signal Health conclusion.

ENG-013C — Signal Health Operational Runtime v1

This runtime combines already-available operational evidence:

- one expected media profile for logical identity;
- one stabilized MediaHealth conclusion;
- one MediaMTXSnapshot for current source evidence;
- one already-derived StreamingMeasurement.

It does not capture MediaMTX, observe media, calculate transport
measurements, stabilize Health, persist events, or own a background loop.
"""

from __future__ import annotations

from app.domain.streaming.expected_media_profile import (
    ExpectedMediaProfile,
)
from app.domain.streaming.media_health import MediaHealth
from app.noc.current_state.media_health_current_state import (
    MediaHealthCurrentState,
)
from app.noc.current_state.media_health_current_state_resolver import (
    MediaHealthCurrentStateResolver,
)
from app.domain.streaming.metrics import StreamingMeasurement
from app.domain.streaming.models import MediaMTXSnapshot
from app.domain.streaming.signal_health import (
    SignalHealth,
    SignalHealthEvaluator,
)
from app.services.source_transport_health_evaluator import (
    SourceTransportHealthEvaluator,
)


class SignalHealthOperationalRuntime:
    """Compose Source Transport Health and Media Health."""

    def __init__(
        self,
        *,
        source_transport_health_evaluator: (
            SourceTransportHealthEvaluator
        ),
        signal_health_evaluator: SignalHealthEvaluator,
        media_health_current_state_resolver: (
            MediaHealthCurrentStateResolver | None
        ) = None,
    ) -> None:
        self._source_transport_health_evaluator = (
            source_transport_health_evaluator
        )
        self._signal_health_evaluator = signal_health_evaluator
        self._media_health_current_state_resolver = (
            media_health_current_state_resolver
        )


    def process_current_state(
        self,
        *,
        profile: ExpectedMediaProfile,
        media_current_state: MediaHealthCurrentState | None,
        media_snapshot: MediaMTXSnapshot,
        measurement: StreamingMeasurement,
    ) -> SignalHealth:
        """Return Signal Health using effective current Media status."""

        resolver = self._media_health_current_state_resolver

        if resolver is None:
            raise RuntimeError(
                "media_health_current_state_resolver is required "
                "for process_current_state"
            )

        if media_snapshot.captured_at != measurement.captured_at:
            raise ValueError(
                "media_snapshot and measurement must belong "
                "to the same capture instant"
            )

        media_path = media_snapshot.get_path(
            profile.path_name
        )

        if media_path is None:
            raise ValueError(
                "media snapshot does not contain "
                f"path {profile.path_name!r}"
            )

        if media_path.source is None:
            raise ValueError(
                "media snapshot path does not contain "
                f"a source for {profile.path_name!r}"
            )

        path_measurement = measurement.get_path(
            profile.path_name
        )

        if path_measurement is None:
            raise ValueError(
                "streaming measurement does not contain "
                f"path {profile.path_name!r}"
            )

        source_transport_health = (
            self._source_transport_health_evaluator.evaluate(
                service_id=profile.service_id,
                source_type=media_path.source.source_type,
                measurement=path_measurement,
            )
        )

        effective_media_status = resolver.resolve(
            state=media_current_state,
            now=media_snapshot.captured_at,
        )

        return self._signal_health_evaluator.evaluate(
            profile_id=profile.profile_id,
            service_id=profile.service_id,
            path_name=profile.path_name,
            media_status=effective_media_status,
            transport_health=source_transport_health,
        )

    def process(
        self,
        *,
        profile: ExpectedMediaProfile,
        media_health: MediaHealth,
        media_snapshot: MediaMTXSnapshot,
        measurement: StreamingMeasurement,
    ) -> SignalHealth:
        """Return one Signal Health conclusion from coherent evidence."""

        if media_snapshot.captured_at != measurement.captured_at:
            raise ValueError(
                "media_snapshot and measurement must belong "
                "to the same capture instant"
            )

        media_path = media_snapshot.get_path(
            profile.path_name
        )

        if media_path is None:
            raise ValueError(
                "media snapshot does not contain "
                f"path {profile.path_name!r}"
            )

        if media_path.source is None:
            raise ValueError(
                "media snapshot path does not contain "
                f"a source for {profile.path_name!r}"
            )

        path_measurement = measurement.get_path(
            profile.path_name
        )

        if path_measurement is None:
            raise ValueError(
                "streaming measurement does not contain "
                f"path {profile.path_name!r}"
            )

        source_transport_health = (
            self._source_transport_health_evaluator.evaluate(
                service_id=profile.service_id,
                source_type=media_path.source.source_type,
                measurement=path_measurement,
            )
        )

        return self._signal_health_evaluator.evaluate(
            media_health=media_health,
            transport_health=source_transport_health,
        )
