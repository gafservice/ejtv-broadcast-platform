# ENG-013B - RTMP Health Evidence

## Scope

This document records the implementation and validation evidence for:

`Block 8 - RTMP Health`

Block 8 extends the observed multiprotocol Health architecture with specialized
RTMP connection Health while preserving the existing SRT Health semantics,
SessionSnapshot population authority and observed-only architecture.

The implementation was developed incrementally through Blocks 8A-8E.

## Architectural boundary

The RTMP Health pipeline is:

```text
MediaMTX /v3/rtmpconns/list
        |
        v
MediaMTXSessionAdapter
        |
        v
ActiveSession
        |
        v
previous/current SessionSnapshot
        |
        v
RTMPConnectionHealthService
        |
        v
RTMPConnectionHealth
        |
        v
StreamingHealthAggregator
        |
        v
ProtocolHealth -> ServiceHealth -> PlatformHealth
        |
        v
DashboardApplication
        |
        v
DashboardSnapshotInput
        |
        v
DashboardService
        |
        v
ActiveConnectionRow.health
        |
        v
CONNECTED CLIENTS / HEALTH
```

Block 8 does not introduce expected-session semantics.

Absence of an RTMP session is not interpreted as failure.

Block 8 does not modify SRT thresholds, SRT stabilization, alarm policy,
event policy, MediaMTX configuration or codec/transcoding behavior.

## Block 8A - RTMP Health domain model

Block 8A introduced the specialized `RTMPConnectionHealth` domain model.

The model carries:

- connection identity;
- path name;
- connection state;
- effective byte delta;
- effective bitrate;
- outbound discarded-frame evidence;
- canonical Health status;
- explanatory message.

The canonical statuses remain `HEALTHY`, `DEGRADED`, `CRITICAL` and `UNKNOWN`.

## Block 8B - Public contract

Block 8B validated the public RTMP Health contract and module-level exposure
without introducing a parallel Health hierarchy.

## Block 8C - Temporal RTMP Health

`RTMPConnectionHealthService` evaluates consecutive observations of the same
compatible RTMP connection.

Temporal identity is based on `session_id` while requiring compatible protocol,
path, role and connection provenance.

The first observation is `UNKNOWN` because no temporal delta exists.

For publishers the effective counter is received bytes.
For readers the effective counter is sent bytes.

A valid positive monotonic delta across a positive observation interval produces
`HEALTHY` evidence.

Zero delta, counter reset, invalid interval or insufficient temporal evidence
remain `UNKNOWN`.

Absolute cumulative byte counters are not interpreted as Health.

Discarded frames remain evidence and do not independently introduce severity
thresholds in Block 8.

Block 8C was committed as:

```text
253b15c feat(streaming): add RTMP temporal health
```

## Block 8D - Aggregation and runtime integration

Block 8D integrates specialized RTMP Health into the existing multiprotocol
aggregation architecture.

`SessionSnapshot` remains the authority for observed population.

Orphan RTMP Health evidence cannot create ghost services or connections.

A unique compatible RTMP Health record takes precedence over generic
`SessionQuality` for the corresponding observed RTMP session.

Specialized `UNKNOWN` is valid evidence and is preserved as `UNKNOWN`; it does
not fall back to generic SessionQuality.

Missing, ambiguous or incompatible specialized evidence uses the existing
generic SessionQuality path for aggregation.

`DashboardApplication` retains the previous SessionSnapshot required for
temporal RTMP evaluation and transports the resulting evidence into the
aggregator.

Block 8D was committed as:

```text
1bd8ace feat(streaming): integrate RTMP health aggregation
```

Physical validation of Block 8D confirmed a real RTMP publisher transition
from `UNKNOWN` on the first observation to `HEALTHY` after a valid positive
byte delta.

The complete backend regression at Block 8D closure completed with:

```text
3280 passed
0 failed
1 warning
```

## Block 8E - RTMP Health presentation

Block 8E exposes already-computed specialized RTMP Health in the existing
`CONNECTED CLIENTS` table.

The presentation transport is:

```text
RTMPConnectionHealth
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
ActiveConnectionRow.health
        |
        v
CONNECTED CLIENTS / HEALTH
```

Matching requires a unique specialized record with both connection identifier
and path matching the observed RTMP session.

Specialized `UNKNOWN` remains `UNKNOWN`.

Ambiguous specialized evidence is not selected arbitrarily and is presented
as `N/A`.

Connections without applicable specialized RTMP Health are presented as `N/A`.

The renderer does not calculate Health.

The existing BITRATE presentation semantics remain unchanged; Block 8E does not
replace SessionMeasurement bitrate with RTMP effective bitrate.

## Physical validation

Physical validation was executed on `ejtv-01` against real simultaneous RTMP
and SRT reader sessions without restarting MediaMTX or disturbing the streams.

Observed sessions included:

```text
impact  RTMP  READER  201.192.154.132:51407
ejtv    SRT   READER  190.115.202.229:46175
```

The RTMP `impact` connection showed a positive real byte delta over five seconds:

```text
Sample A bytesSent: 3870108931
Sample B bytesSent: 3872576889
Delta:              2467958 bytes
```

The terminal dashboard physically rendered:

```text
CLIENT   PROTOCOL   ROLE     HEALTH
ejtv     SRT        READER   N/A
impact   RTMP       READER   HEALTHY
```

The same dashboard reported:

```text
Active clients: SRT 1 / RTMP 1 / TOTAL 2
Platform Health: HEALTHY
Services:        2
Coverage:        100%
H:2 D:0 C:0 U:0
```

This confirms the complete RTMP Health presentation path while preserving the
non-RTMP presentation behavior.

## Codec boundary observed during validation

RTMP Health describes observed transport activity; it does not validate media
track completeness or codec compatibility.

Therefore an RTMP connection can be `HEALTHY` under the current contract even
when a video track is unavailable to an RTMP reader.

Codec normalization, transcoding and future Media/Track Health remain outside
Block 8.

## Automated validation

Block 8E focused and dashboard regression completed with:

```text
DashboardApplication         27 passed
DashboardService             54 passed
DashboardSnapshotService      6 passed
Dashboard renderers          18 passed
Dashboard suite             389 passed
```

The complete backend regression completed with:

```text
3284 passed
0 failed
1 warning
67.84 seconds
```

The remaining warning is the previously known Starlette/httpx TestClient
deprecation warning and is unrelated to Block 8.

Structural validation completed cleanly with:

```text
git diff --check
```

## Block 8 result

Block 8 successfully adds specialized observed RTMP Health from temporal
evaluation through multiprotocol aggregation and terminal presentation.

The implementation preserves SessionSnapshot population authority, specialized
`UNKNOWN`, observed-only semantics, SRT behavior and separation between domain
Health logic and presentation.

Physical validation and complete automated regression are green.

Formal closure requires final documentation integration, diff review, commit,
push and verification that local and origin are synchronized.
