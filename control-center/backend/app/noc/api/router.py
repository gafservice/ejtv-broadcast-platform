"""HTTP API for the NOC Node SDK.

ENG-013B — Node SDK API

This API surface exposes the logical Node inventory, current
NodeInstance snapshots, durable history queries, and derived history
exports without placing domain or operational policy inside the HTTP layer.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import (
    get_history_csv_export_service,
    get_history_query_service,
    get_node_registry,
    get_snapshot_service,
)
from app.api.schemas.noc_history import (
    HistoryCsvExportRequest,
)
from app.api.security import require_permission
from app.core.config import Settings, get_settings
from app.core.responses import success_response
from app.noc.domain.node import Node
from app.noc.domain.node_instance import NodeInstance
from app.noc.registry.registry import NodeRegistry
from app.noc.serializers.snapshot_serializer import SnapshotSerializer
from app.noc.history.alarm_transition import AlarmTransition
from app.noc.history.event_history_record import EventHistoryRecord
from app.noc.services.history_csv_export_service import (
    HistoryCsvExportService,
)
from app.noc.services.history_query_service import (
    HistoryQueryService,
)
from app.noc.services.snapshot_service import SnapshotService


router = APIRouter(
    prefix="/noc",
    tags=["NOC"],
    dependencies=[
        Depends(
            require_permission(
                "dashboard.read"
            )
        )
    ],
)


def _require_node(
    registry: NodeRegistry,
    node_id: str,
) -> Node:
    """Resolve a Node from its canonical textual identifier."""

    for node in registry.list_nodes():
        if node.node_id.id == node_id:
            return node

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Node {node_id!r} no está registrado.",
    )


def _require_instance(
    node: Node,
    instance_id: str,
) -> NodeInstance:
    """Resolve a NodeInstance within its parent Node."""

    for instance in node.instances:
        if str(instance.instance_id) == instance_id:
            return instance

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=(
            f"NodeInstance {instance_id!r} no está registrado "
            f"en Node {node.node_id.id!r}."
        ),
    )


def _serialize_node(
    node: Node,
) -> dict[str, object]:
    """Serialize the public logical Node summary."""

    return {
        "node_id": node.node_id.id,
        "name": node.node_id.name,
        "display_name": node.node_id.display_name,
        "node_type": node.node_type.value,
        "instance_count": node.instance_count,
    }


def _serialize_instance(
    instance: NodeInstance,
) -> dict[str, object]:
    """Serialize the public NodeInstance summary."""

    return {
        "instance_id": str(
            instance.instance_id
        ),
        "created_at": (
            instance.created_at
            .isoformat()
            .replace("+00:00", "Z")
        ),
    }


def _serialize_utc_timestamp(value) -> str:
    """Serialize canonical UTC timestamp."""

    return value.isoformat().replace("+00:00", "Z")


def _serialize_event_history_record(
    record: EventHistoryRecord,
) -> dict[str, object]:
    """Serialize one durable historical event."""

    event = record.event

    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "severity": event.severity.value,
        "timestamp": _serialize_utc_timestamp(
            event.timestamp
        ),
        "source": str(event.source),
        "title": event.title,
        "description": event.description,
        "attributes": (
            dict(event.attributes)
            if event.attributes is not None
            else None
        ),
        "correlation_id": event.correlation_id,
        "recorded_at": _serialize_utc_timestamp(
            record.recorded_at
        ),
    }


def _serialize_alarm_transition(
    transition: AlarmTransition,
) -> dict[str, object]:
    """Serialize one durable alarm transition."""

    return {
        "transition_id": transition.transition_id,
        "alarm_id": transition.alarm_id,
        "transition_type": transition.transition_type.value,
        "timestamp": _serialize_utc_timestamp(
            transition.timestamp
        ),
        "source": str(transition.source),
        "state": transition.state.value,
        "actor": transition.actor,
        "metadata": (
            dict(transition.metadata)
            if transition.metadata is not None
            else None
        ),
    }


@router.get(
    "/nodes",
    status_code=status.HTTP_200_OK,
    summary="Lista los Nodes registrados en el NOC",
)
def list_nodes(
    request: Request,
    registry: NodeRegistry = Depends(
        get_node_registry
    ),
) -> dict[str, object]:
    """Return the logical Node inventory."""

    nodes = registry.list_nodes()

    return success_response(
        data={
            "nodes": [
                _serialize_node(node)
                for node in nodes
            ],
            "total": len(nodes),
        },
        message="Nodes del NOC obtenidos correctamente.",
        request_id=request.state.request_id,
    )


@router.get(
    "/nodes/{node_id}",
    status_code=status.HTTP_200_OK,
    summary="Obtiene un Node registrado",
)
def get_node(
    node_id: str,
    request: Request,
    registry: NodeRegistry = Depends(
        get_node_registry
    ),
) -> dict[str, object]:
    """Return one logical Node."""

    node = _require_node(
        registry,
        node_id,
    )

    return success_response(
        data=_serialize_node(node),
        message="Node del NOC obtenido correctamente.",
        request_id=request.state.request_id,
    )


@router.get(
    "/nodes/{node_id}/instances",
    status_code=status.HTTP_200_OK,
    summary="Lista las instancias de un Node",
)
def list_node_instances(
    node_id: str,
    request: Request,
    registry: NodeRegistry = Depends(
        get_node_registry
    ),
) -> dict[str, object]:
    """Return all runtime instances belonging to one Node."""

    node = _require_node(
        registry,
        node_id,
    )

    instances = node.instances

    return success_response(
        data={
            "node_id": node.node_id.id,
            "instances": [
                _serialize_instance(instance)
                for instance in instances
            ],
            "total": len(instances),
        },
        message="Instancias del Node obtenidas correctamente.",
        request_id=request.state.request_id,
    )


@router.get(
    "/nodes/{node_id}/instances/{instance_id}/snapshot",
    status_code=status.HTTP_200_OK,
    summary="Obtiene el Snapshot actual de una NodeInstance",
)
def get_node_instance_snapshot(
    node_id: str,
    instance_id: str,
    request: Request,
    registry: NodeRegistry = Depends(
        get_node_registry
    ),
    snapshot_service: SnapshotService = Depends(
        get_snapshot_service
    ),
) -> dict[str, object]:
    """Build and return the current canonical NodeSnapshot."""

    node = _require_node(
        registry,
        node_id,
    )

    instance = _require_instance(
        node,
        instance_id,
    )

    snapshot = snapshot_service.build(
        node.node_id,
        instance.instance_id,
    )

    payload = SnapshotSerializer().to_dict(
        snapshot
    )

    return success_response(
        data=payload,
        message="Snapshot del Node obtenido correctamente.",
        request_id=request.state.request_id,
    )


@router.post(
    "/nodes/{node_id}/instances/{instance_id}/history/exports/csv",
)
def export_instance_history_csv(
    node_id: str,
    instance_id: str,
    payload: HistoryCsvExportRequest,
    request: Request,
    registry: NodeRegistry = Depends(get_node_registry),
    history_csv_export_service: HistoryCsvExportService = Depends(
        get_history_csv_export_service
    ),
    settings: Settings = Depends(get_settings),
):
    """Generate one derived CSV export for a NodeInstance history range."""

    node = _require_node(
        registry,
        node_id,
    )

    instance = _require_instance(
        node,
        instance_id,
    )

    export_id = uuid4().hex
    destination = (
        Path(settings.noc_csv_export_path)
        / export_id
    )

    result = history_csv_export_service.export_range(
        start=payload.start,
        end=payload.end,
        destination=destination,
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    return success_response(
        data={
            "export_id": export_id,
            "format": "csv",
            "node_id": node.node_id.id,
            "instance_id": str(
                instance.instance_id
            ),
            "window": {
                "start": _serialize_utc_timestamp(
                    payload.start
                ),
                "end": _serialize_utc_timestamp(
                    payload.end
                ),
            },
            "files": [
                result.events_file.name,
                result.alarm_transitions_file.name,
            ],
        },
        message=(
            "Exportación CSV histórica generada correctamente."
        ),
        request_id=request.state.request_id,
    )


@router.get(
    "/nodes/{node_id}/instances/{instance_id}/history/24h",
    status_code=status.HTTP_200_OK,
    summary="Obtiene el histórico operacional de las últimas 24 horas",
)
def get_node_instance_history_24h(
    node_id: str,
    instance_id: str,
    request: Request,
    registry: NodeRegistry = Depends(
        get_node_registry
    ),
    history_query_service: HistoryQueryService = Depends(
        get_history_query_service
    ),
) -> dict[str, object]:
    """Return durable operational history from the last 24 hours."""

    node = _require_node(
        registry,
        node_id,
    )

    instance = _require_instance(
        node,
        instance_id,
    )

    history = history_query_service.last_24_hours(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    return success_response(
        data={
            "node_id": node.node_id.id,
            "instance_id": str(
                instance.instance_id
            ),
            "window": {
                "start": _serialize_utc_timestamp(
                    history.start
                ),
                "end": _serialize_utc_timestamp(
                    history.end
                ),
                "duration_hours": 24,
            },
            "events": [
                _serialize_event_history_record(record)
                for record in history.events
            ],
            "alarm_transitions": [
                _serialize_alarm_transition(transition)
                for transition in history.alarm_transitions
            ],
            "totals": {
                "events": len(history.events),
                "alarm_transitions": len(
                    history.alarm_transitions
                ),
            },
        },
        message=(
            "Histórico operacional de 24 horas "
            "obtenido correctamente."
        ),
        request_id=request.state.request_id,
    )
