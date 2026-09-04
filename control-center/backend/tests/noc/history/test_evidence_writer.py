"""Tests for canonical NOC evidence serialization."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from app.noc.domain.node_alarm import (
    AlarmState,
)
from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.alarm_transition import (
    AlarmTransition,
    AlarmTransitionType,
)
from app.noc.history.event_history_record import (
    EventHistoryRecord,
)
from app.noc.history.evidence_writer import (
    EVIDENCE_SCHEMA_VERSION,
    EvidenceWriter,
    alarm_transition_evidence_payload,
    event_evidence_payload,
    serialize_alarm_transition_evidence,
    serialize_event_evidence,
)


INSTANCE_ID = NodeInstanceId(
    "streaming-primary"
)

NODE_ID = NodeId.create(
    id="streaming-core",
    name="streaming",
    display_name="Streaming Core",
)


def test_serialize_event_evidence() -> None:
    timestamp = datetime(
        2026,
        9,
        1,
        16,
        45,
        tzinfo=timezone.utc,
    )

    event = EventRecord(
        event_id="event-001",
        event_type="SESSION_CONNECTED",
        severity=EventSeverity.INFO,
        timestamp=timestamp,
        source=INSTANCE_ID,
        title="SRT reader connected on ejtv",
        description="Reader session connected.",
        attributes={
            "path": "ejtv",
            "protocol": "SRT",
            "role": "READER",
        },
        correlation_id="corr-001",
    )

    record = EventHistoryRecord(
        event=event,
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        recorded_at=timestamp,
    )

    encoded = serialize_event_evidence(
        record
    )

    payload = json.loads(encoded)

    assert payload == {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "record_type": "event",
        "event_id": "event-001",
        "event_type": "SESSION_CONNECTED",
        "severity": "INFO",
        "timestamp": "2026-09-01T16:45:00Z",
        "source": "streaming-primary",
        "node_id": "streaming-core",
        "instance_id": "streaming-primary",
        "title": "SRT reader connected on ejtv",
        "description": "Reader session connected.",
        "attributes": {
            "path": "ejtv",
            "protocol": "SRT",
            "role": "READER",
        },
        "correlation_id": "corr-001",
        "recorded_at": "2026-09-01T16:45:00Z",
    }

    assert "\n" not in encoded


def test_serialize_alarm_transition_evidence() -> None:
    timestamp = datetime(
        2026,
        9,
        1,
        16,
        50,
        tzinfo=timezone.utc,
    )

    transition = AlarmTransition(
        transition_id="alarm-transition-test-001",
        alarm_id="CRITICAL_PATH_TRAFFIC_STALLED:ejtv",
        transition_type=AlarmTransitionType.OPENED,
        timestamp=timestamp,
        source=INSTANCE_ID,
        state=AlarmState.ACTIVE,
        actor="noc-runtime",
        metadata={
            "path": "ejtv",
            "reason": "inbound bitrate is zero",
        },
    )

    encoded = serialize_alarm_transition_evidence(
        transition
    )

    payload = json.loads(encoded)

    assert payload == {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "record_type": "alarm_transition",
        "transition_id": "alarm-transition-test-001",
        "alarm_id": "CRITICAL_PATH_TRAFFIC_STALLED:ejtv",
        "transition_type": "OPENED",
        "timestamp": "2026-09-01T16:50:00Z",
        "source": "streaming-primary",
        "state": "ACTIVE",
        "actor": "noc-runtime",
        "metadata": {
            "path": "ejtv",
            "reason": "inbound bitrate is zero",
        },
    }

    assert "\n" not in encoded


def test_event_serialization_is_deterministic() -> None:
    timestamp = datetime(
        2026,
        9,
        1,
        16,
        45,
        tzinfo=timezone.utc,
    )

    event = EventRecord(
        event_id="event-001",
        event_type="SESSION_CONNECTED",
        severity=EventSeverity.INFO,
        timestamp=timestamp,
        source=INSTANCE_ID,
        title="Connected",
        description="Connected.",
        attributes={
            "z": "last",
            "a": "first",
        },
    )

    record = EventHistoryRecord(
        event=event,
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        recorded_at=timestamp,
    )

    first = serialize_event_evidence(record)
    second = serialize_event_evidence(record)

    assert first == second


def test_evidence_writer_is_runtime_protocol() -> None:
    class Writer:
        def append_event(self, record) -> None:
            return None

        def append_alarm_transition(
            self,
            transition,
        ) -> None:
            return None

    assert isinstance(
        Writer(),
        EvidenceWriter,
    )

def test_event_evidence_payload_matches_serialized_payload() -> None:
    timestamp = datetime(
        2026,
        9,
        1,
        17,
        0,
        tzinfo=timezone.utc,
    )

    record = EventHistoryRecord(
        event=EventRecord(
            event_id="event-payload-001",
            event_type="SESSION_CONNECTED",
            severity=EventSeverity.INFO,
            timestamp=timestamp,
            source=INSTANCE_ID,
            title="Connected",
            description="Reader connected.",
            attributes={
                "z": "last",
                "a": "first",
            },
            correlation_id="corr-payload-001",
        ),
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        recorded_at=timestamp,
    )

    payload = event_evidence_payload(record)

    assert payload == json.loads(
        serialize_event_evidence(record)
    )
    assert payload["attributes"] == {
        "z": "last",
        "a": "first",
    }


def test_alarm_transition_evidence_payload_matches_serialized_payload() -> None:
    timestamp = datetime(
        2026,
        9,
        1,
        17,
        5,
        tzinfo=timezone.utc,
    )

    transition = AlarmTransition(
        transition_id="alarm-transition-payload-001",
        alarm_id="CRITICAL_PATH_TRAFFIC_STALLED:ejtv",
        transition_type=AlarmTransitionType.OPENED,
        timestamp=timestamp,
        source=INSTANCE_ID,
        state=AlarmState.ACTIVE,
        actor="noc-runtime",
        metadata={
            "z": "last",
            "a": "first",
        },
    )

    payload = alarm_transition_evidence_payload(
        transition
    )

    assert payload == json.loads(
        serialize_alarm_transition_evidence(
            transition
        )
    )
    assert payload["metadata"] == {
        "z": "last",
        "a": "first",
    }


def test_event_evidence_payload_rejects_invalid_record() -> None:
    with pytest.raises(
        TypeError,
        match="EventHistoryRecord",
    ):
        event_evidence_payload(object())


def test_alarm_transition_evidence_payload_rejects_invalid_transition() -> None:
    with pytest.raises(
        TypeError,
        match="AlarmTransition",
    ):
        alarm_transition_evidence_payload(
            object()
        )
