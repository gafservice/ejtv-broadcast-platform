"""Normalize MediaMTX connection metrics without evaluating Health.

ENG-013C — Transport Quality Producer v1.

This producer consumes an existing metrics snapshot. It does not
perform HTTP requests, infer UDP ingress quality, or generate alarms.
"""

from __future__ import annotations

from datetime import datetime
from math import isfinite

from app.adapters.mediamtx.metrics_parser import (
    MediaMTXMetricsSnapshot,
)
from app.domain.sessions import (
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.domain.streaming.evidence_acquisition_interval import (
    EvidenceAcquisitionInterval,
)
from app.domain.streaming.media_observation import (
    EvidenceAvailability,
)
from app.domain.streaming.transport_quality_observation import (
    TransportMetricObservation,
    TransportQualityObservation,
)


class TransportQualityProducer:
    """Build normalized transport evidence from an existing snapshot."""

    def build(
        self,
        *,
        snapshot: MediaMTXMetricsSnapshot,
        observed_at: datetime,
        service_id: str,
        path_name: str,
        source_type: str,
        source_id: str | None = None,
        session_snapshot: SessionSnapshot | None = None,
        acquisition_interval: EvidenceAcquisitionInterval | None = None,
    ) -> TransportQualityObservation:
        """Produce SRT connection RTT evidence for one requested path."""

        metrics: list[TransportMetricObservation] = []

        for sample in snapshot.find(
            "srt_conns_ms_rtt",
            path=path_name,
        ):
            connection_id = sample.labels.get("id", "").strip()

            if not connection_id:
                continue

            if not isfinite(sample.value):
                continue

            role = self._resolve_connection_role(
                connection_id=connection_id,
                path_name=path_name,
                state=sample.labels.get("state", ""),
                session_snapshot=session_snapshot,
                acquisition_interval=acquisition_interval,
            )

            metrics.append(
                TransportMetricObservation(
                    metric_name="srt.connection.rtt",
                    value=sample.value,
                    unit="ms",
                    availability=EvidenceAvailability.AVAILABLE,
                    source="mediamtx.metrics",
                    direction=None,
                    connection_id=connection_id,
                    connection_role=role,
                    measurement_scope="CONNECTION",
                )
            )

        # SRT receive-quality metrics remain connection-scoped.
        # They are not automatically attributable to source ingress.
        receive_families = (
            (
                "srt_conns_packets_received_loss",
                "srt.connection.receive.loss_packets",
                "packets",
            ),
            (
                "srt_conns_ms_receive_tsb_pd_delay",
                "srt.connection.receive.tsbpd_delay",
                "ms",
            ),
            (
                "srt_conns_packets_received_retrans",
                "srt.connection.receive.retransmitted_packets",
                "packets",
            ),
        )

        for family, metric_name, unit in receive_families:
            for sample in snapshot.find(
                family,
                path=path_name,
            ):
                connection_id = sample.labels.get("id", "").strip()

                if not connection_id:
                    continue

                if not isfinite(sample.value):
                    continue

                # Receive packet-loss evidence is a packet count.
                # TSBPD receive delay is a nonnegative duration.
                if sample.value < 0:
                    continue

                if (
                    family in (
                        "srt_conns_packets_received_loss",
                        "srt_conns_packets_received_retrans",
                    )
                    and not sample.value.is_integer()
                ):
                    continue

                role = self._resolve_connection_role(
                    connection_id=connection_id,
                    path_name=path_name,
                    state=sample.labels.get("state", ""),
                    session_snapshot=session_snapshot,
                    acquisition_interval=acquisition_interval,
                )

                metrics.append(
                    TransportMetricObservation(
                        metric_name=metric_name,
                        value=sample.value,
                        unit=unit,
                        availability=EvidenceAvailability.AVAILABLE,
                        source="mediamtx.metrics",
                        direction=None,
                        connection_id=connection_id,
                        connection_role=role,
                        measurement_scope="CONNECTION",
                    )
                )

        # Preserve independent connections while rejecting every
        # occurrence of an ambiguous metric identity.
        #
        # This identity must remain aligned with the immutable domain
        # contract in TransportQualityObservation.
        identity_counts = {}

        for metric in metrics:
            identity = (
                metric.metric_name,
                metric.source,
                metric.direction,
                metric.connection_id,
                metric.connection_role,
                metric.measurement_scope,
            )

            identity_counts[identity] = (
                identity_counts.get(identity, 0) + 1
            )

        duplicate_identities = {
            identity
            for identity, count in identity_counts.items()
            if count > 1
        }

        if duplicate_identities:
            metrics = [
                metric
                for metric in metrics
                if (
                    metric.metric_name,
                    metric.source,
                    metric.direction,
                    metric.connection_id,
                    metric.connection_role,
                    metric.measurement_scope,
                ) not in duplicate_identities
            ]

        return TransportQualityObservation(
            service_id=service_id,
            path_name=path_name,
            source_type=source_type,
            source_id=source_id,
            observed_at=observed_at,
            availability=(
                EvidenceAvailability.AVAILABLE
                if metrics
                else EvidenceAvailability.UNAVAILABLE
            ),
            metrics=tuple(metrics),
            acquisition_interval=acquisition_interval,
        )

    @staticmethod
    def _resolve_connection_role(
        *,
        connection_id: str,
        path_name: str,
        state: str,
        session_snapshot: SessionSnapshot | None,
        acquisition_interval: EvidenceAcquisitionInterval | None = None,
    ) -> SessionRole:
        """Correlate only an SRT session on the same path."""

        if session_snapshot is None:
            return SessionRole.UNKNOWN

        matches = [
            session
            for session in session_snapshot.sessions
            if session.session_id == connection_id
            and session.protocol is SessionProtocol.SRT
            and session.path == path_name
        ]

        if len(matches) != 1:
            return SessionRole.UNKNOWN

        normalized_state = state.strip().lower()

        expected_roles = {
            "read": SessionRole.READER,
            "publish": SessionRole.PUBLISHER,
        }

        expected_role = expected_roles.get(normalized_state)

        if expected_role is None:
            return SessionRole.UNKNOWN

        session = matches[0]

        if (
            acquisition_interval is not None
            and session.connected_since > acquisition_interval.completed_at
        ):
            return SessionRole.UNKNOWN

        if session.role is not expected_role:
            return SessionRole.UNKNOWN

        normalized_session_state = session.state.strip().lower()

        reader_states = {
            "read",
            "reader",
            "reading",
        }

        publisher_states = {
            "publish",
            "publisher",
            "publishing",
        }

        if normalized_session_state in reader_states:
            session_state_role = SessionRole.READER
        elif normalized_session_state in publisher_states:
            session_state_role = SessionRole.PUBLISHER
        else:
            session_state_role = SessionRole.UNKNOWN

        if session_state_role is not expected_role:
            return SessionRole.UNKNOWN

        return session.role
