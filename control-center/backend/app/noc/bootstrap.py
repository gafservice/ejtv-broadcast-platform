"""Runtime bootstrap for the NOC Node SDK.

ENG-013B — Node SDK

The bootstrap establishes the minimum canonical Node identity required
by the local Control Center runtime.

It intentionally does not infer operational state, health, availability,
metrics, alarms or heartbeat information.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_type import NodeType
from app.noc.infrastructure.system_info_provider import (
    LinuxSystemInfoProvider,
)
from app.noc.infrastructure.system_metrics_provider import (
    SystemMetricsProvider,
)
from app.noc.services.metric_service import MetricService
from app.services.system_service import SystemService
from app.noc.registry.registry import NodeRegistry


DEFAULT_NODE_ID = "streaming-core"
DEFAULT_NODE_NAME = "streaming"
DEFAULT_NODE_DISPLAY_NAME = "Streaming Core"
DEFAULT_INSTANCE_ID = "streaming-primary"


class NocBootstrapStatus(StrEnum):
    """Possible NOC runtime bootstrap outcomes."""

    CREATED = "CREATED"
    INSTANCE_ADDED = "INSTANCE_ADDED"
    ALREADY_EXISTS = "ALREADY_EXISTS"


@dataclass(frozen=True, slots=True)
class NocBootstrapResult:
    """Result of one NOC runtime bootstrap execution."""

    status: NocBootstrapStatus
    node: Node

    @property
    def created(self) -> bool:
        return self.status is NocBootstrapStatus.CREATED

    @property
    def changed(self) -> bool:
        return self.status in {
            NocBootstrapStatus.CREATED,
            NocBootstrapStatus.INSTANCE_ADDED,
        }


def bootstrap_noc_runtime(
    registry: NodeRegistry,
) -> NocBootstrapResult:
    """Ensure the canonical local streaming Node exists.

    The operation is idempotent:

    - if the Node does not exist, create it with its primary instance;
    - if the Node exists but the primary instance is absent, add it;
    - if both already exist, make no changes.

    No operational state is synthesized.
    """

    if not isinstance(registry, NodeRegistry):
        raise TypeError(
            "registry must be a NodeRegistry"
        )

    existing = _find_existing_node(
        registry
    )

    if existing is None:
        node = Node(
            node_id=NodeId.create(
                id=DEFAULT_NODE_ID,
                name=DEFAULT_NODE_NAME,
                display_name=DEFAULT_NODE_DISPLAY_NAME,
            ),
            node_type=NodeType.STREAMING,
        )

        node.create_instance(
            instance_id=DEFAULT_INSTANCE_ID
        )

        registry.register(node)

        return NocBootstrapResult(
            status=NocBootstrapStatus.CREATED,
            node=node,
        )

    _validate_existing_identity(
        existing
    )

    if _has_primary_instance(existing):
        return NocBootstrapResult(
            status=NocBootstrapStatus.ALREADY_EXISTS,
            node=existing,
        )

    existing.create_instance(
        instance_id=DEFAULT_INSTANCE_ID
    )

    registry.repository.save(
        existing
    )

    return NocBootstrapResult(
        status=NocBootstrapStatus.INSTANCE_ADDED,
        node=existing,
    )


def _find_existing_node(
    registry: NodeRegistry,
) -> Node | None:
    for node in registry.list_nodes():
        if node.node_id.id == DEFAULT_NODE_ID:
            return node

    return None


def _validate_existing_identity(
    node: Node,
) -> None:
    """Reject reuse of the canonical NodeId for another NodeType."""

    if node.node_type is not NodeType.STREAMING:
        raise RuntimeError(
            f"Canonical Node {DEFAULT_NODE_ID!r} already exists "
            f"with incompatible NodeType {node.node_type.value!r}"
        )


def _has_primary_instance(
    node: Node,
) -> bool:
    return any(
        str(instance.instance_id)
        == DEFAULT_INSTANCE_ID
        for instance in node.instances
    )


def initialize_noc_runtime_info(
    registry: NodeRegistry,
    provider: LinuxSystemInfoProvider | None = None,
) -> None:
    """Populate NodeInfo for the canonical local runtime instance.

    This operation observes the execution environment after the canonical
    Node identity has been bootstrapped.

    It does not synthesize status, health, availability, metrics, alarms
    or heartbeat information.
    """

    if not isinstance(registry, NodeRegistry):
        raise TypeError(
            "registry must be a NodeRegistry"
        )

    if (
        provider is not None
        and not isinstance(
            provider,
            LinuxSystemInfoProvider,
        )
    ):
        raise TypeError(
            "provider must be a LinuxSystemInfoProvider or None"
        )

    node = _find_existing_node(
        registry
    )

    if node is None:
        raise RuntimeError(
            "Canonical NOC Node must be bootstrapped "
            "before runtime information is initialized"
        )

    _validate_existing_identity(
        node
    )

    instance = next(
        (
            item
            for item in node.instances
            if str(item.instance_id)
            == DEFAULT_INSTANCE_ID
        ),
        None,
    )

    if instance is None:
        raise RuntimeError(
            "Canonical NOC Node does not contain "
            f"instance {DEFAULT_INSTANCE_ID!r}"
        )

    system_info_provider = (
        provider
        or LinuxSystemInfoProvider()
    )

    instance.info = system_info_provider.collect(
        instance.instance_id
    )

    registry.repository.save(
        node
    )


def initialize_noc_runtime_metrics(
    registry: NodeRegistry,
    system_service: SystemService,
    metric_service: MetricService,
    provider: SystemMetricsProvider | None = None,
) -> None:
    """Collect and publish current host metrics for the canonical instance."""

    if not isinstance(registry, NodeRegistry):
        raise TypeError(
            "registry must be a NodeRegistry"
        )

    if not isinstance(system_service, SystemService):
        raise TypeError(
            "system_service must be a SystemService"
        )

    if not isinstance(metric_service, MetricService):
        raise TypeError(
            "metric_service must be a MetricService"
        )

    if (
        provider is not None
        and not isinstance(
            provider,
            SystemMetricsProvider,
        )
    ):
        raise TypeError(
            "provider must be a SystemMetricsProvider or None"
        )

    node = _find_existing_node(
        registry
    )

    if node is None:
        raise RuntimeError(
            "Canonical NOC Node must be bootstrapped "
            "before runtime metrics are initialized"
        )

    instance = next(
        (
            item
            for item in node.instances
            if str(item.instance_id)
            == DEFAULT_INSTANCE_ID
        ),
        None,
    )

    if instance is None:
        raise RuntimeError(
            "Canonical NOC Node does not contain "
            f"instance {DEFAULT_INSTANCE_ID!r}"
        )

    resources = (
        system_service.get_system_resources()
    )

    samples = (
        provider
        or SystemMetricsProvider()
    ).collect(
        resources
    )

    for sample in samples:
        metric_service.receive(
            node.node_id,
            instance.instance_id,
            sample,
        )
