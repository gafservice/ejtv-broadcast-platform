# ENG-013B - Platform Health Dashboard Evidence

## Scope

This document records the implementation and validation evidence for:

`Block 7 - DASHBOARD`

Block 7 exposes the observed multiprotocol `PlatformHealth` domain introduced
by Block 6 in the existing terminal dashboard.

The dashboard evolves incrementally without moving operational Health logic
into the presentation layer and without replacing the existing specialized
`STREAM HEALTH` or `NODE HEALTH` panels.

## Architectural boundary

The presentation pipeline is:

```text
SessionSnapshot
      |
      v
StreamingHealthAggregator
      |
      v
PlatformHealth
      |
      v
DashboardApplication
      |
      v
DashboardSnapshotInput
      |
      v
DashboardSnapshotService
      |
      v
DashboardService
      |
      v
PlatformHealthPanelData
      |
      v
PlatformHealthRenderer
      |
      v
PLATFORM HEALTH panel
```

The dashboard does not calculate aggregate Health.

Block 7 does not capture MediaMTX independently, stabilize Health, resolve
aggregation policy, infer expected presence, create Events, create Alarms,
or introduce protocol-specific RTMP, RTSP, HLS or WebRTC Health semantics.

## Presentation model

Block 7 introduces `PlatformHealthPanelData`.

The presentation model carries:

- aggregate status;
- worst observed status;
- healthy population count;
- degraded population count;
- critical population count;
- unknown population count;
- evidence coverage;
- affected fraction;
- observed service count;
- timezone-aware capture timestamp.

Presentation validation rejects negative counters, fractions outside the
inclusive range `[0.0, 1.0]`, and timezone-naive capture timestamps.

`None` remains valid for `evidence_coverage` and `affected_fraction` when
the underlying observed population makes those values undefined.

The presentation model does not recompute Health.

## Dashboard service projection

`DashboardService` projects the domain `PlatformHealth` into
`PlatformHealthPanelData`.

The projection preserves status, worst observed status, population counts,
service count, evidence coverage, affected fraction and capture timestamp.

No aggregation rule is duplicated in the dashboard service.

## Snapshot and application transport

`DashboardSnapshotInput` accepts `PlatformHealth | None`.

`DashboardSnapshotService` transports the object to `DashboardService`.

`DashboardApplication` transports the already-computed
`latest_platform_health` produced by the Block 6 aggregator.

No second MediaMTX capture, aggregation pass or Health evaluation is added.

## Renderer

Block 7 introduces `PlatformHealthRenderer`.

The panel displays:

- Status;
- Worst;
- Services;
- Coverage;
- Affected;
- H / D / C / U population counts.

Undefined fractions are rendered as `N/A`.

When Platform Health is unavailable, the panel explicitly renders `UNKNOWN`.

The renderer does not calculate Health status from population counters.

## Incremental dashboard layout

The historical top summary row remains:

```text
SERVER | STREAMING | STREAM HEALTH | NODE HEALTH
```

`PLATFORM HEALTH` is integrated into the lower summary row.

With session information present:

```text
SYSTEM | ACTIVE CLIENTS | PLATFORM HEALTH
```

This preserves the established width of `STREAM HEALTH` and avoids the
wrapping regression detected during Block 7 layout testing.

## Separation of Health domains

The dashboard now exposes three distinct operational views:

```text
STREAM HEALTH
PLATFORM HEALTH
NODE HEALTH
```

`STREAM HEALTH` remains the specialized SRT-oriented diagnostic view.

`PLATFORM HEALTH` represents the observed multiprotocol hierarchy from
connection to protocol to service to platform.

`NODE HEALTH` represents server and node operational Health.

These concepts remain independent.

## Temporal provenance discovered during physical validation

The first physical Block 7 execution exposed an invalid temporal assumption.

The runtime captures MediaMTX state and normalized session state sequentially.

Physical timestamps were:

```text
MediaMTXSnapshot : 2026-09-09 21:30:41.709130+00:00
SessionSnapshot  : 2026-09-09 21:30:41.714707+00:00
Delta            : 5.577 ms
```

`StreamingMeasurement` derives from `MediaMTXSnapshot` and preserves that
capture timestamp.

The existing specialized `StreamingHealth` also remains associated with the
MediaMTX capture timestamp.

`PlatformHealth`, however, derives from `SessionSnapshot` and correctly
preserves `SessionSnapshot.captured_at`.

The initial dashboard integration incorrectly required both capture times
to be exactly equal.

## Temporal correction

The fix removes only the invalid equality requirement between
`PlatformHealth.captured_at` and `MediaMTXSnapshot.captured_at`.

The existing equality contracts between MediaMTX snapshot, streaming
measurement and specialized Streaming Health remain unchanged.

No arbitrary timestamp tolerance was introduced.

A regression test reproduces the physical 5.577 ms separation and verifies
that the Platform Health timestamp is preserved independently.

## Physical validation

After the temporal correction, the real terminal dashboard on `ejtv-01`
started and rendered all Health views successfully.

Observed Platform Health:

```text
Status:   HEALTHY
Worst:    HEALTHY
Services: 2
Coverage: 100%
Affected: 0%
H:2 D:0 C:0 U:0
```

MediaMTX exposed three paths:

```text
ejtv
enlace
impact
```

Only two observed SRT reader sessions participated in Platform Health:

```text
ejtv
impact
```

Therefore `PLATFORM HEALTH` reported two services rather than three.

The `enlace` path did not create ghost Health population without an observed
multimedia session.

This physically confirms the Block 6 observed-only invariant:

```text
ABSENCE != FAILURE
```

After physical validation MediaMTX remained active, the existing Uvicorn
process remained active, and only `live_monitor` was stopped.

## Automated validation

Focused regression completed with:

```text
Dashboard models             25 passed
Dashboard service            52 passed
Dashboard snapshot service    5 passed
Dashboard application        26 passed
Platform Health renderer      3 passed
Dashboard renderer           17 passed
live_monitor composition      3 passed
Block 6 aggregation          69 passed
```

The complete backend regression completed with:

```text
3249 passed
0 failed
1 warning
65.16 seconds
```

The remaining warning is the previously known Starlette/httpx test-client
deprecation warning and is unrelated to Block 7.

Structural validation completed cleanly:

```text
python -m compileall -q app tests
git diff --check
```

## Environment note

The first complete-regression attempt stopped during collection because the
active virtual environment did not contain `reportlab`.

The project already declared `reportlab>=4.0,<5.0` in `requirements.txt`.

The environment was repaired by installing the already-declared dependency.
`reportlab 4.5.1` and its Pillow dependency were installed.

No dependency declaration or application source change was required.

The subsequent complete backend regression passed all 3249 tests.

## Block 7 result

Block 7 successfully exposes the Block 6 aggregation domain in the existing
terminal dashboard while preserving architectural separation between domain
Health logic and presentation.

Physical validation and complete automated regression are green.

Formal closure still requires documentation integration, final diff review,
commit, push and verification that local and origin are synchronized.
