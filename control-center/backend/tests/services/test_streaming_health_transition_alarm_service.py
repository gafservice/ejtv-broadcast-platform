"""Tests for Stream Health transition alarm coordination.

ENG-013B — Stream Health Contract Block 5

The coordinator consumes one already-detected StreamingHealthTransition,
asks alarm policy for a lifecycle decision, and delegates lifecycle
operations to the existing AlarmService.

It must not detect Stream Health transitions itself.
"""

from datetime import UTC, datetime, timedelta

from app.domain.streaming.health import (
    HealthStatus,
    StreamingHealth,
)
from app.noc.domain.node import Node
from app.noc.domain.node_alarm import AlarmState
from app.noc.services.alarm_service import (
    AlarmDisposition,
    AlarmService,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import NodeRegistry
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.streaming_health_alarm_policy import (
    StreamingHealthAlarmAction,
    StreamingHealthAlarmDecision,
    StreamingHealthAlarmPolicy,
)
from app.services.streaming_health_transition_alarm_factory import (
    StreamingHealthTransitionAlarmFactory,
)
from app.services.streaming_health_transition_alarm_service import (
    StreamingHealthTransitionAlarmService,
)
from app.services.streaming_health_transition_detector import (
    StreamingHealthTransition,
)


class MemoryRepository:
    def __init__(self):
        self.nodes = {}

    def save(self, node):
        self.nodes[node.node_id.id] = node

    def get(self, node_id):
        return self.nodes.get(node_id.id)

    def exists(self, node_id):
        return node_id.id in self.nodes

    def list_all(self):
        return tuple(self.nodes.values())

    def delete(self, node_id):
        return self.nodes.pop(node_id.id, None) is not None

    def count(self):
        return len(self.nodes)


BASE_TIME = datetime(
    2026,
    9,
    8,
    12,
    0,
    tzinfo=UTC,
)

NODE_ID = NodeId.create(
    id="streaming-node",
    name="streaming-node",
    display_name="Streaming Node",
)

INSTANCE_ID = NodeInstanceId(
    "streaming-primary"
)


def health(status: HealthStatus) -> StreamingHealth:
    return StreamingHealth(
        captured_at=BASE_TIME,
        paths=(),
        status=status,
        message=f"stream health is {status.value}",
    )


def transition(
    previous: HealthStatus,
    current: HealthStatus,
    kind: HealthTransitionKind,
) -> StreamingHealthTransition:
    return StreamingHealthTransition(
        previous=health(previous),
        current=health(current),
        kind=kind,
    )


class RaisePolicy(StreamingHealthAlarmPolicy):
    """Controlled test policy proving the RAISE integration path."""

    def evaluate(
        self,
        *,
        transition,
    ) -> StreamingHealthAlarmDecision:
        return StreamingHealthAlarmDecision(
            action=StreamingHealthAlarmAction.RAISE,
            transition=transition,
        )


class ResolvePolicy(StreamingHealthAlarmPolicy):
    def evaluate(
        self,
        *,
        transition,
    ) -> StreamingHealthAlarmDecision:
        return StreamingHealthAlarmDecision(
            action=StreamingHealthAlarmAction.RESOLVE,
            transition=transition,
        )


class KeepPolicy(StreamingHealthAlarmPolicy):
    def evaluate(
        self,
        *,
        transition,
    ) -> StreamingHealthAlarmDecision:
        return StreamingHealthAlarmDecision(
            action=StreamingHealthAlarmAction.KEEP,
            transition=transition,
        )


def make_context(
    *,
    policy: StreamingHealthAlarmPolicy | None = None,
):
    repository = MemoryRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NODE_ID,
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id=INSTANCE_ID.value
    )

    registry.register(node)

    alarm_service = AlarmService(registry)

    service = StreamingHealthTransitionAlarmService(
        alarm_service=alarm_service,
        policy=policy,
        factory=StreamingHealthTransitionAlarmFactory(),
    )

    return (
        node,
        instance,
        alarm_service,
        service,
    )


def critical_transition():
    return transition(
        HealthStatus.HEALTHY,
        HealthStatus.CRITICAL,
        HealthTransitionKind.DEGRADED,
    )


def recovery_transition():
    return transition(
        HealthStatus.CRITICAL,
        HealthStatus.HEALTHY,
        HealthTransitionKind.RECOVERED,
    )


def test_none_transition_is_noop():
    _, _, alarm_service, service = make_context()

    result = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=None,
        timestamp=BASE_TIME,
    )

    assert result.transition is None
    assert result.decision.action is StreamingHealthAlarmAction.NONE
    assert result.alarm is None
    assert result.receipt is None
    assert alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    ) == ()


def test_production_policy_does_not_raise_from_critical_alone():
    _, _, alarm_service, service = make_context()

    value = critical_transition()

    result = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=value,
        timestamp=BASE_TIME,
    )

    assert result.transition is value
    assert result.decision.action is StreamingHealthAlarmAction.NONE
    assert result.alarm is None
    assert result.receipt is None
    assert alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    ) == ()


def test_authorized_raise_uses_existing_alarm_service():
    _, _, alarm_service, service = make_context(
        policy=RaisePolicy(),
    )

    value = critical_transition()

    result = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=value,
        timestamp=BASE_TIME,
    )

    assert result.transition is value
    assert result.decision.action is StreamingHealthAlarmAction.RAISE
    assert result.receipt is not None
    assert result.receipt.disposition is AlarmDisposition.RAISED
    assert result.alarm is result.receipt.alarm
    assert result.alarm is not None
    assert result.alarm.alarm_type == "STREAM_HEALTH"
    assert result.alarm.state is AlarmState.ACTIVE

    assert alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    ) == (result.alarm,)


def test_authorized_raise_does_not_duplicate_active_stream_alarm():
    _, _, alarm_service, service = make_context(
        policy=RaisePolicy(),
    )

    value = critical_transition()

    first = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=value,
        timestamp=BASE_TIME,
    )

    second = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=value,
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    assert first.receipt is not None
    assert second.receipt is None
    assert second.alarm is first.alarm

    active = alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    )

    assert len(active) == 1
    assert active[0].alarm_type == "STREAM_HEALTH"


def test_keep_preserves_existing_stream_alarm():
    _, _, alarm_service, raise_service = make_context(
        policy=RaisePolicy(),
    )

    opened = raise_service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical_transition(),
        timestamp=BASE_TIME,
    )

    keep_service = StreamingHealthTransitionAlarmService(
        alarm_service=alarm_service,
        policy=KeepPolicy(),
        factory=StreamingHealthTransitionAlarmFactory(),
    )

    result = keep_service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=transition(
            HealthStatus.CRITICAL,
            HealthStatus.DEGRADED,
            HealthTransitionKind.IMPROVED,
        ),
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    assert opened.alarm is not None
    assert result.decision.action is StreamingHealthAlarmAction.KEEP
    assert result.receipt is None
    assert result.alarm == opened.alarm
    assert result.alarm.state is AlarmState.ACTIVE


def test_recovery_resolves_existing_active_stream_alarm():
    _, _, alarm_service, raise_service = make_context(
        policy=RaisePolicy(),
    )

    opened = raise_service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical_transition(),
        timestamp=BASE_TIME,
    )

    assert opened.alarm is not None

    resolve_service = StreamingHealthTransitionAlarmService(
        alarm_service=alarm_service,
        policy=ResolvePolicy(),
        factory=StreamingHealthTransitionAlarmFactory(),
    )

    result = resolve_service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=recovery_transition(),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert result.decision.action is StreamingHealthAlarmAction.RESOLVE
    assert result.receipt is not None
    assert result.receipt.disposition is AlarmDisposition.RESOLVED
    assert result.alarm is result.receipt.alarm
    assert result.alarm is not None
    assert result.alarm.state is AlarmState.RESOLVED

    assert alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    ) == ()


def test_production_recovery_resolves_preexisting_stream_alarm():
    _, _, alarm_service, raise_service = make_context(
        policy=RaisePolicy(),
    )

    opened = raise_service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical_transition(),
        timestamp=BASE_TIME,
    )

    assert opened.alarm is not None

    production_service = StreamingHealthTransitionAlarmService(
        alarm_service=alarm_service,
        factory=StreamingHealthTransitionAlarmFactory(),
    )

    result = production_service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=recovery_transition(),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert result.decision.action is StreamingHealthAlarmAction.RESOLVE
    assert result.receipt is not None
    assert result.receipt.disposition is AlarmDisposition.RESOLVED
    assert result.alarm is not None
    assert result.alarm.state is AlarmState.RESOLVED


def test_resolve_without_existing_alarm_is_noop():
    _, _, alarm_service, service = make_context(
        policy=ResolvePolicy(),
    )

    result = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=recovery_transition(),
        timestamp=BASE_TIME,
    )

    assert result.decision.action is StreamingHealthAlarmAction.RESOLVE
    assert result.alarm is None
    assert result.receipt is None
    assert alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    ) == ()


def test_authorized_raise_does_not_duplicate_acknowledged_stream_alarm():
    _, _, alarm_service, raise_service = make_context(
        policy=RaisePolicy(),
    )

    opened = raise_service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical_transition(),
        timestamp=BASE_TIME,
    )

    assert opened.alarm is not None

    acknowledged = alarm_service.acknowledge(
        NODE_ID,
        INSTANCE_ID,
        opened.alarm.alarm_id,
        acknowledged_by="operator",
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    assert acknowledged.alarm.state is AlarmState.ACKNOWLEDGED

    repeated = raise_service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical_transition(),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert repeated.receipt is None
    assert repeated.alarm is acknowledged.alarm

    active = alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    )

    assert len(active) == 1
    assert active[0].alarm_id == opened.alarm.alarm_id
    assert active[0].state is AlarmState.ACKNOWLEDGED


def test_recovery_resolves_acknowledged_stream_alarm_preserving_ack():
    _, _, alarm_service, raise_service = make_context(
        policy=RaisePolicy(),
    )

    opened = raise_service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical_transition(),
        timestamp=BASE_TIME,
    )

    assert opened.alarm is not None

    acknowledged = alarm_service.acknowledge(
        NODE_ID,
        INSTANCE_ID,
        opened.alarm.alarm_id,
        acknowledged_by="operator",
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    assert acknowledged.alarm.state is AlarmState.ACKNOWLEDGED
    assert acknowledged.alarm.acknowledged is True

    production_service = StreamingHealthTransitionAlarmService(
        alarm_service=alarm_service,
        factory=StreamingHealthTransitionAlarmFactory(),
    )

    result = production_service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=recovery_transition(),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert result.decision.action is StreamingHealthAlarmAction.RESOLVE
    assert result.receipt is not None
    assert result.receipt.disposition is AlarmDisposition.RESOLVED

    assert result.alarm is not None
    assert result.alarm.state is AlarmState.RESOLVED
    assert result.alarm.acknowledged is True
    assert result.alarm.acknowledged_by == "operator"
    assert result.alarm.acknowledged_at == (
        BASE_TIME + timedelta(seconds=5)
    )

    assert alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    ) == ()
