"""HTTP API for the NOC Node SDK.

ENG-013B — Node SDK API

This first API surface is intentionally read-only. It exposes the
logical Node inventory and current NodeInstance snapshots without
placing domain or operational policy inside the HTTP layer.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import (
    get_node_registry,
    get_snapshot_service,
)
from app.api.security import require_permission
from app.core.responses import success_response
from app.noc.domain.node import Node
from app.noc.domain.node_instance import NodeInstance
from app.noc.registry.registry import NodeRegistry
from app.noc.serializers.snapshot_serializer import SnapshotSerializer
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
