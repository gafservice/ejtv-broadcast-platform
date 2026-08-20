"""Event coordination service for the NOC.

ENG-013B — Node SDK
NCS reference: 17-NODE-EVENT.md

EventService coordinates persistence and retrieval of EventRecord objects
belonging to registered NodeInstances.

EventRecord is immutable. Events represent historical operational facts and
are therefore appended to the NodeInstance event collection.

Event detection policy does not belong here. Other components decide when an
operational condition should generate an event.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.noc.domain.node_event import (
    EventRecord,
    NodeEvent,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import (
    NodeInstance,
    NodeInstanceId,
)
from app.noc.registry.registry import NodeRegistry


class EventServiceError(Exception):
    """Base error raised by EventService."""


class NodeInstanceNotFoundError(EventServiceError):
    """Raised when a NodeInstance cannot be found."""


class DuplicateEventError(EventServiceError):
    """Raised when an event_id already exists."""


class EventSourceMismatchError(EventServiceError):
    """Raised when an event belongs to another NodeInstance."""


class EventDisposition(str, Enum):
    """Result of an EventService operation."""

    RECORDED = "RECORDED"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EventReceipt:
    """Result returned after recording an event."""

    disposition: EventDisposition
    event: EventRecord


class EventService:
    """Coordinate events for registered NodeInstances."""

    def __init__(self, registry: NodeRegistry) -> None:
        if not isinstance(registry, NodeRegistry):
            raise TypeError(
                "registry must be a NodeRegistry"
            )

        self._registry = registry

    @property
    def registry(self) -> NodeRegistry:
        return self._registry

    def record(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        event: EventRecord,
    ) -> EventReceipt:
        """Append one immutable operational event."""

        instance, node = self._resolve_instance(
            node_id,
            instance_id,
        )

        if not isinstance(event, EventRecord):
            raise TypeError(
                "event must be an EventRecord"
            )

        if event.source != instance_id:
            raise EventSourceMismatchError(
                "EventRecord.source does not match NodeInstance"
            )

        records = self._records(instance)

        if self._find(records, event.event_id) is not None:
            raise DuplicateEventError(
                f"event {event.event_id!r} already exists"
            )

        instance.events = records + (event,)

        self._registry.repository.save(node)

        return EventReceipt(
            disposition=EventDisposition.RECORDED,
            event=event,
        )

    def current(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> NodeEvent:
        """Return the current immutable event collection."""

        instance, _ = self._resolve_instance(
            node_id,
            instance_id,
        )

        return NodeEvent(
            events=self._records(instance)
        )

    def get(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        event_id: str,
    ) -> EventRecord | None:
        """Return one event by identifier."""

        instance, _ = self._resolve_instance(
            node_id,
            instance_id,
        )

        return self._find(
            self._records(instance),
            event_id,
        )

    def list_all(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> tuple[EventRecord, ...]:
        """Return all recorded events."""

        instance, _ = self._resolve_instance(
            node_id,
            instance_id,
        )

        return self._records(instance)

    def _resolve_instance(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> tuple[NodeInstance, object]:
        if not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId"
            )

        if not isinstance(
            instance_id,
            NodeInstanceId,
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

        node = self._registry.require(
            node_id
        )

        instance = self._find_instance(
            node.instances,
            instance_id,
        )

        if instance is None:
            raise NodeInstanceNotFoundError(
                f"NodeInstance {instance_id!s} is not registered "
                f"under Node {node_id.id!r}"
            )

        return instance, node

    @staticmethod
    def _find_instance(
        instances: tuple[NodeInstance, ...],
        instance_id: NodeInstanceId,
    ) -> NodeInstance | None:
        for instance in instances:
            if instance.instance_id == instance_id:
                return instance

        return None

    @staticmethod
    def _records(
        instance: NodeInstance,
    ) -> tuple[EventRecord, ...]:
        records = getattr(
            instance,
            "events",
            (),
        )

        if not isinstance(records, tuple):
            raise EventServiceError(
                "NodeInstance.events must be a tuple"
            )

        for event in records:
            if not isinstance(event, EventRecord):
                raise EventServiceError(
                    "NodeInstance.events must contain EventRecord objects"
                )

        return records

    @staticmethod
    def _find(
        records: tuple[EventRecord, ...],
        event_id: str,
    ) -> EventRecord | None:
        normalized = EventService._normalize_event_id(
            event_id
        )

        for event in records:
            if event.event_id == normalized:
                return event

        return None

    @staticmethod
    def _normalize_event_id(
        event_id: str,
    ) -> str:
        if not isinstance(event_id, str):
            raise TypeError(
                "event_id must be a string"
            )

        normalized = event_id.strip()

        if not normalized:
            raise ValueError(
                "event_id must not be empty"
            )

        return normalized
