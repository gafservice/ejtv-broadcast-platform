# ENG-013B - Stream Health Aggregation Evidence

## Scope

This document records the implementation and validation evidence for:

`Block 6 - AGGREGATION`

Block 6 evolves the existing Stream Health domain from specialized
connection/path observations toward an observed multiprotocol hierarchy:

```text
connection
→ protocol
→ service
→ platform
```

The block aggregates observed Health without introducing expected-presence
semantics, alarm authorization, persistence policy or presentation logic.

The canonical streaming Health states remain:

- `HEALTHY`
- `DEGRADED`
- `CRITICAL`
- `UNKNOWN`

Block 6 does not redefine the specialized SRT Health evaluator or its
temporal stabilization.

## Architectural boundary

The aggregation pipeline is:

```text
SessionSnapshot
      │
      ├── observed membership / service / protocol / role
      └── SessionQuality fallback
                     │
                     ▼
        effective StreamingHealth
        specialized SRT evidence
                     │
                     ▼
          StreamingHealthAggregator
                     │
                     ▼
             ProtocolHealth
                     │
                     ▼
              ServiceHealth
                     │
                     ▼
             PlatformHealth
```

`SessionSnapshot` is the authority for observed population and scope.

Specialized SRT Health may enrich an already-observed SRT session when a
valid connection match exists. Specialized Health does not create sessions,
services or protocol populations that are absent from `SessionSnapshot`.

The aggregator does not capture MediaMTX, stabilize Health, detect
transitions, create Events, create Alarms or persist evidence.

## Domain components

### `HealthPopulation`

`HealthPopulation` records the number of observed members in each canonical
Health state:

- `healthy_count`
- `degraded_count`
- `critical_count`
- `unknown_count`

Derived values include:

- `known_count`
- `total_count`
- `affected_count`
- `affected_fraction`
- `evidence_coverage`

Negative population counts are rejected.

`affected_fraction` is undefined when there is no known evidence.

`evidence_coverage` is undefined when there is no observed population.

### `ProtocolHealth`

`ProtocolHealth` represents Health for one observed protocol within one
service.

It preserves service identity, protocol, population, role counts, aggregate
Health status, worst observed Health status and a diagnostic message.

Role counts must equal the total observed protocol population.

### `ServiceHealth`

`ServiceHealth` aggregates the observed protocol Health objects belonging to
one service.

All child protocol objects must belong to the same service and duplicate
protocols are rejected.

Its population is the sum of the child protocol populations.

### `PlatformHealth`

`PlatformHealth` represents the observed service hierarchy at one
timezone-aware capture instant.

Its population is the sum of the child service populations.

Duplicate service identifiers are rejected.

An empty observed platform is `UNKNOWN`, not `HEALTHY` and not `CRITICAL`.

## Aggregation semantics

Block 6 intentionally avoids arbitrary percentage thresholds.

For a population with known evidence:

```text
if known_count == 0:
    UNKNOWN
elif healthy_count == known_count:
    HEALTHY
elif critical_count > 0 and healthy_count == 0:
    CRITICAL
else:
    DEGRADED
```

`UNKNOWN` does not dominate known evidence.

Examples:

```text
H H H       → HEALTHY
H H D       → DEGRADED
H H C       → DEGRADED
H C C       → DEGRADED
D D D       → DEGRADED
D D C       → CRITICAL
C C C       → CRITICAL
H H U U U   → HEALTHY
D U U U     → DEGRADED
C U U U     → CRITICAL
U U U       → UNKNOWN
```

The worst observed state is retained separately from the aggregate state.

Therefore one observed `CRITICAL` member can produce:

```text
aggregate_status=DEGRADED
worst_observed_status=CRITICAL
```

when healthy population remains present.

## Hierarchical propagation

Aggregation is deliberately hierarchical.

Connection observations are first grouped by:

```text
(service_id, protocol)
```

Protocol Health is resolved from its observed connections.

Service Health is resolved from the child `ProtocolHealth.status` values.

Platform Health is resolved from the child `ServiceHealth.status` values.

Population counters continue to represent the underlying observed
connections at every level.

Services are ordered deterministically by `service_id`.

Protocols are ordered deterministically by canonical protocol value.

## Service identity

Observed service membership comes from the normalized session path.

When a session has no path, the existing canonical unassigned service
identity is preserved:

```text
(sin path)
```

Specialized SRT evidence is not allowed to move an unassigned session into a
different service.

## Specialized SRT precedence

For an observed SRT session, Block 6 attempts to use the already-effective
specialized `SRTConnectionHealth`.

A specialized match is accepted only when:

- the observed session is SRT;
- the connection identifier matches the observed session identifier;
- the observed session has a verifiable path;
- the specialized connection path matches that observed path;
- exactly one valid specialized connection matches.

When specialized evidence is absent, ambiguous or incompatible with the
observed session scope, aggregation falls back to the existing normalized
`SessionQuality`.

The generic mapping is:

```text
EXCELLENT → HEALTHY
GOOD      → HEALTHY
FAIR      → DEGRADED
POOR      → DEGRADED
CRITICAL  → CRITICAL
UNKNOWN   → UNKNOWN
```

Orphan specialized SRT evidence does not create population.

## Expected presence boundary

Block 6 aggregates what is observed.

It does not infer what should have been present.

The invariant is:

```text
ABSENCE != FAILURE
```

A dynamic reader that disappears does not automatically create a failed
service or protocol.

Expected presence remains an explicit policy concern.

Critical-path semantics, operational impact and common-cause reasoning also
remain outside the base aggregation model.

## Multiprotocol boundary

The aggregation domain accepts the existing canonical protocols:

- SRT
- RTMP
- RTSP
- HLS
- WebRTC
- UNKNOWN

Block 6 does not copy SRT thresholds into other protocols.

SRT can use its existing specialized Health evidence.

Other protocols use the already-normalized `SessionQuality` until their
protocol-specific Health evidence is introduced by later controlled blocks.

`SessionProtocol.UNKNOWN` remains valid observed population and is not
discarded.

## DashboardApplication integration

`DashboardApplication` integrates aggregation after the effective
`StreamingHealth` has been resolved.

The aggregator receives:

- the same `SessionSnapshot` already captured for the dashboard cycle;
- the effective `StreamingHealth` already produced by the existing SRT
  Health pipeline.

No second MediaMTX capture is performed.

No second SRT evaluation or temporal stabilization is performed.

The resulting aggregate is exposed independently through:

```text
latest_platform_health
```

The existing specialized `latest_health` contract remains intact.

This preserves the distinction between specialized SRT Health and observed
multiprotocol Platform Health.

## Runtime composition

`live_monitor` creates one `StreamingHealthAggregator` and injects it into
`DashboardApplication`.

The composition does not introduce a new capture loop, persistence path,
transition detector or alarm runtime.

## Presentation boundary

Block 6 intentionally does not render `PlatformHealth` in the terminal
dashboard.

The current renderer continues to consume the existing specialized
`StreamingHealth` and node Health contracts.

Presentation of the new aggregation domain belongs to Block 7 - DASHBOARD.

This avoids coupling aggregation semantics to the current SRT-oriented
presentation model.

## Automated validation

The aggregation domain suite completed with:

```text
69 passed
42 test function definitions
duplicates = {}
```

Focused integration regression completed with:

```text
225 passed
```

covering the aggregation domain, `DashboardApplication`, `live_monitor`,
snapshot/service/renderer behavior and Session/Streaming Health services.

The complete backend regression completed with:

```text
3228 passed
0 failed
1 warning
65.86 seconds
```

The remaining warning is the previously known Starlette/httpx test-client
deprecation warning and is unrelated to Block 6.

Additional structural validation completed cleanly:

```text
python -m compileall -q app tests
git diff --check
```

## Acceptance coverage

The completed test matrix covers:

- empty observed population;
- generic `SessionQuality` fallback;
- specialized SRT precedence;
- canonical protocol identity;
- canonical Health states at protocol, service and platform levels;
- multiprotocol hierarchical aggregation;
- `UNKNOWN` evidence coexisting with known evidence;
- all-UNKNOWN population;
- SRT path mismatch fallback;
- orphan specialized SRT evidence;
- ambiguous specialized SRT matches;
- sessions without path using `(sin path)`;
- prevention of specialized-path inheritance when session path is absent;
- observed `SessionProtocol.UNKNOWN` population;
- critical known evidence not diluted by UNKNOWN population;
- empty specialized SRT Health fallback;
- degraded plus critical population without healthy members resolving to
  `CRITICAL`;
- `DashboardApplication` aggregation from the effective Health snapshot;
- runtime composition through `live_monitor`.

## Physical validation

An isolated physical observer was executed on 2026-09-09 against the live
MediaMTX runtime.

The observer intentionally avoided `DashboardApplication.run_once` and its
event/alarm side effects.

It used the real MediaMTX session adapter, metrics parser,
`StreamingHealthService` and `StreamingHealthAggregator`.

Observed sessions:

```text
service=ejtv
protocol=SRT
role=READER
remote=190.115.202.229:46175
quality=GOOD

service=impact
protocol=SRT
role=READER
remote=201.192.154.132:48352
quality=GOOD
```

Effective specialized SRT Health:

```text
status=HEALTHY
paths=2
ejtv   HEALTHY  connections=1  rtt_ms≈7.69
impact HEALTHY  connections=1  rtt_ms≈1.35
```

Resulting observed Platform Health:

```text
status=HEALTHY
worst_observed_status=HEALTHY
healthy_count=2
degraded_count=0
critical_count=0
unknown_count=0
total_count=2
evidence_coverage=1.0
affected_fraction=0.0
```

The service hierarchy contained exactly the two observed services:

```text
ejtv   → SRT → HEALTHY → readers=1
impact → SRT → HEALTHY → readers=1
```

No ghost services were introduced.

No Event, Alarm, JSONL or SQLite evidence writes were requested by the
isolated observer.

The existing `live_monitor`, MediaMTX and Uvicorn processes remained active.

## Block boundary

Block 6 does not implement:

- expected-presence policy;
- alarm authorization from aggregate state;
- common-cause analysis;
- service-impact policy;
- protocol-specific RTMP, RTSP, HLS or WebRTC Health evaluators;
- PlatformHealth Events or Alarms;
- PlatformHealth persistence;
- PlatformHealth dashboard rendering;
- ENG-014 functionality.

Those concerns remain assigned to their later controlled blocks.

## Current result

The Block 6 implementation, automated regression and physical validation are
complete.

This evidence document records the validated aggregation contract and its
current integration boundary.

Final Block 6 closure still requires final diff review, explicit staging,
commit, push and verification that local and origin are synchronized.
