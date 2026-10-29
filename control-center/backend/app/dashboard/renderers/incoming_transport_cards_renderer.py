"""Six-card TRANSPORT presentation for INCOMING V2.

Presentation only: no health evaluation or metric inference.
"""

from __future__ import annotations

from datetime import timezone

from rich.panel import Panel
from rich.table import Table

from app.dashboard.models.incoming_panel import IncomingPanelData
from app.domain.sessions.protocol import SessionRole
from app.domain.streaming.media_observation import (
    EvidenceAvailability,
)
from app.domain.streaming.transport_quality_observation import (
    TransportMetricObservation,
    TransportQualityObservation,
)


class IncomingTransportCardsRenderer:
    """Render available incoming transport evidence."""

    @staticmethod
    def _select_transport_quality_observation(
        observations: tuple[TransportQualityObservation, ...],
        *,
        path_name: str | None,
        source_type: str | None,
        source_id: str | None = None,
    ) -> TransportQualityObservation | None:
        """Select unique path/type/source-compatible evidence.

        Matching absent IDs does not prove physical source identity.
        """

        if not path_name or not source_type:
            return None

        matches = tuple(
            observation
            for observation in observations
            if observation.path_name == path_name
            and observation.source_type == source_type
            and observation.source_id == source_id
        )

        if len(matches) != 1:
            return None

        return matches[0]

    @staticmethod
    def _select_srt_ingress_rtt_candidate(
        observation: TransportQualityObservation,
    ) -> TransportMetricObservation | None:
        """Identify a candidate, not proven ingress RTT."""

        if observation.source_type != "srtConn":
            return None

        if observation.availability is not EvidenceAvailability.AVAILABLE:
            return None

        candidates = []

        for metric in observation.metrics:
            if metric.metric_name != "srt.connection.rtt":
                continue

            if metric.connection_role is SessionRole.UNKNOWN:
                return None

            if metric.connection_role is None:
                return None

            if metric.connection_role is SessionRole.READER:
                continue

            if metric.connection_role is not SessionRole.PUBLISHER:
                return None

            if metric.availability is not EvidenceAvailability.AVAILABLE:
                return None

            if metric.unit != "ms":
                return None

            if metric.measurement_scope != "CONNECTION":
                return None

            if not metric.connection_id:
                return None

            if metric.value is None:
                return None

            candidates.append(metric)

        if len(candidates) != 1:
            return None

        return candidates[0]

    @staticmethod
    def _select_srt_ingress_rtt_attributed(
        observation: TransportQualityObservation,
    ) -> TransportMetricObservation | None:
        """Apply a conservative source-identity gate to SRT RTT."""

        candidate = (
            IncomingTransportCardsRenderer
            ._select_srt_ingress_rtt_candidate(observation)
        )

        if candidate is None:
            return None

        if observation.source_id is None:
            return None

        if candidate.connection_id is None:
            return None

        if observation.source_id != candidate.connection_id:
            return None

        return candidate

    @staticmethod
    def _select_srt_ingress_receive_metric(
        observation: TransportQualityObservation,
        *,
        metric_name: str,
        unit: str,
    ) -> TransportMetricObservation | None:
        """Select uniquely attributable SRT ingress receive evidence."""

        if observation.source_type != "srtConn":
            return None

        if observation.availability is not EvidenceAvailability.AVAILABLE:
            return None

        if observation.source_id is None:
            return None

        matches = []

        for metric in observation.metrics:
            if metric.metric_name != metric_name:
                continue

            if metric.connection_role is not SessionRole.PUBLISHER:
                return None

            if metric.availability is not EvidenceAvailability.AVAILABLE:
                return None

            if metric.unit != unit:
                return None

            if metric.measurement_scope != "CONNECTION":
                return None

            if metric.connection_id != observation.source_id:
                return None

            if metric.value is None or metric.value < 0:
                return None

            if unit == "packets" and not float(metric.value).is_integer():
                return None

            matches.append(metric)

        if len(matches) != 1:
            return None

        return matches[0]

    @staticmethod
    def _available(value: object | None) -> str:
        if value is None or value == "":
            return "N/A"
        return str(value)

    @staticmethod
    def _format_bitrate(value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value:.2f} Mbps"

    @staticmethod
    def _format_bytes(value: int | None) -> str:
        if value is None:
            return "N/A"
        return f"{value:,} bytes"

    @staticmethod
    def _format_availability(value: bool | None) -> str:
        if value is None:
            return "N/A"
        return "YES" if value else "NO"

    @staticmethod
    def _format_observed_at(value) -> str:
        if value is None:
            return "N/A"

        if value.tzinfo is None or value.utcoffset() is None:
            return "N/A"

        utc_value = value.astimezone(timezone.utc)
        return utc_value.strftime("%Y-%m-%d %H:%M:%S UTC")

    @staticmethod
    def _format_evidence_age(observed_at, reference_at) -> str:
        if observed_at is None or reference_at is None:
            return "N/A"

        if observed_at.tzinfo is None or reference_at.tzinfo is None:
            return "N/A"

        seconds = (reference_at - observed_at).total_seconds()

        if seconds < 0:
            return "N/A"

        total_seconds = int(seconds)

        if total_seconds >= 3600:
            hours = total_seconds // 3600
            return f"{hours}h"

        if total_seconds >= 60:
            minutes = total_seconds // 60
            return f"{minutes}m"

        return f"{total_seconds}s"

    @staticmethod
    def _card(
        title: str,
        fields: tuple[tuple[str, str], ...],
    ) -> Panel:
        table = Table(
            show_header=False,
            show_edge=False,
            box=None,
            expand=False,
            padding=(0, 1),
        )

        table.add_column(
            "Field",
            style="bold",
            no_wrap=True,
        )

        table.add_column(
            "Value",
            overflow="ellipsis",
        )

        for label, value in fields:
            table.add_row(label, value)

        return Panel(
            table,
            title=title,
            expand=True,
        )

    def render(
        self,
        data: IncomingPanelData | None,
        *,
        selected_path_name: str | None = None,
        compact: bool = False,
        transport_quality_observations: tuple[
            TransportQualityObservation, ...
        ] = (),
    ) -> Panel:
        selected = None

        if data is not None and selected_path_name is not None:
            selected = next(
                (
                    row
                    for row in data.rows
                    if row.path_name == selected_path_name
                ),
                None,
            )

        if selected is None:
            return Panel(
                "No incoming signal selected.",
                title="TRANSPORT DETAIL",
            )

        selected_quality_observation = (
            self._select_transport_quality_observation(
                transport_quality_observations,
                path_name=selected.path_name,
                source_type=selected.transport_source_type,
                source_id=getattr(selected, "transport_source_id", None),
            )
        )

        available = self._available

        rtt_value = "N/A"

        if selected_quality_observation is not None:
            attributed_rtt = self._select_srt_ingress_rtt_attributed(
                selected_quality_observation
            )

            if attributed_rtt is not None:
                rtt_value = f"{attributed_rtt.value:.2f} ms"

        packet_loss_value = "N/A"
        reception_delay_value = "N/A"

        if selected_quality_observation is not None:
            packet_loss = self._select_srt_ingress_receive_metric(
                selected_quality_observation,
                metric_name="srt.connection.receive.loss_packets",
                unit="packets",
            )

            reception_delay = self._select_srt_ingress_receive_metric(
                selected_quality_observation,
                metric_name="srt.connection.receive.tsbpd_delay",
                unit="ms",
            )

            if packet_loss is not None:
                packet_loss_value = f"{int(packet_loss.value)} packets"

            if reception_delay is not None:
                reception_delay_value = f"{reception_delay.value:.2f} ms"

        bitrate = (
            f"{selected.bitrate_receive_mbps:.2f} Mbps"
            if selected.bitrate_receive_mbps is not None
            else "N/A"
        )

        transport_health = (
            selected.transport_health_status.value
            if selected.transport_health_status is not None
            else "N/A"
        )

        if compact:
            compact_table = Table(
                show_header=False,
                show_edge=False,
                box=None,
                expand=False,
                padding=(0, 1),
            )

            compact_table.add_column(
                "Field",
                style="bold",
                no_wrap=True,
            )

            compact_table.add_column(
                "Value",
                overflow="ellipsis",
            )

            for label, value in (
                ("Path", selected.path_name),
                ("Protocol", available(selected.protocol)),
                (
                    "Remote / Expected",
                    available(selected.remote_address),
                ),
                ("Path Status", available(selected.status)),
                ("Receive", bitrate),
                ("Transport Health", transport_health),
                ("Packet Loss", packet_loss_value),
                ("RTT", rtt_value),
            ):
                compact_table.add_row(label, value)

            return Panel(
                compact_table,
                title="TRANSPORT DETAIL",
            )

        connection = self._card(
            "CONNECTION",
            (
                ("Path", selected.path_name),
                ("Protocol", available(selected.protocol)),
                (
                    "Remote / Expected",
                    available(selected.remote_address),
                ),
                ("Path Status", available(selected.status)),
                ("Connection Mode", available(selected.transport_source_type)),
            ),
        )

        traffic = self._card(
            "TRAFFIC",
            (
                ("Receive", bitrate),
                ("Average", self._format_bitrate(selected.bitrate_average_mbps)),
                ("Minimum", self._format_bitrate(selected.bitrate_minimum_mbps)),
                ("Maximum", self._format_bitrate(selected.bitrate_maximum_mbps)),
                ("Received Data", self._format_bytes(selected.transport_received_bytes)),
            ),
        )

        packet_quality = self._card(
            "PACKET QUALITY",
            (
                ("Packet Loss", packet_loss_value),
                ("Retransmissions", "N/A"),
                ("Jitter", "N/A"),
                ("TS Continuity", "N/A"),
            ),
        )

        latency = self._card(
            "LATENCY",
            (
                ("RTT", rtt_value),
                ("SRT Latency", "N/A"),
                ("Network One-Way", "N/A"),
                ("Reception Delay", reception_delay_value),
            ),
        )

        stability = self._card(
            "STABILITY",
            (
                ("Uptime", "N/A"),
                ("Reconnections", "N/A"),
                ("Interruptions", "N/A"),
                ("Availability", self._format_availability(selected.transport_available)),
            ),
        )

        health = self._card(
            "TRANSPORT HEALTH",
            (
                ("Status", transport_health),
                ("Reason", "N/A"),
                ("Evidence Age", self._format_evidence_age(selected.transport_observed_at, data.reference_at)),
                ("Last Evaluation", self._format_observed_at(selected.transport_observed_at)),
                ("Duration", "N/A"),
            ),
        )

        content = Table.grid(
            padding=(0, 1),
            expand=True,
        )

        content.add_column(ratio=1)
        content.add_column(ratio=1)

        content.add_row(connection, traffic)
        content.add_row(packet_quality, latency)
        content.add_row(stability, health)

        return Panel(
            content,
            title="TRANSPORT DETAIL",
        )
