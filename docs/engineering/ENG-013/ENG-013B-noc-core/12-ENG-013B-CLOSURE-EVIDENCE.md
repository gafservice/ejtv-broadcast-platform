# ENG-013B — Final Closure Evidence

## 1. Purpose

This document consolidates the evidence required for formal closure of
ENG-013B — NOC Core.

It does not introduce new runtime behavior.

It records the implemented architecture, automated verification,
physical validation, operational audit and remaining version-control
steps required by the ENG-013B Definition of Done.

---

## 2. Closure state

Current state:

    CLOSURE CANDIDATE

Functional implementation for the current ENG-013B scope is complete.

Formal closure remains pending until:

1. final full backend regression passes;
2. documentation diff is reviewed;
3. selective staging is performed;
4. closure commit is created;
5. branch is pushed;
6. local and origin synchronization is verified.

ENG-014 remains out of scope until those steps are complete.

---

## 3. Implemented NOC foundation

ENG-013B reuses and extends the Node SDK architecture established by
ENG-013A.

Implemented operational areas include:

- Node registry and repository;
- Node Health;
- Node Availability;
- Node Capability;
- Node Capacity;
- Node Metric;
- Node Event;
- Node Alarm;
- Node Heartbeat;
- Node Snapshot;
- validation and serialization;
- durable History/Evidence;
- network interface health;
- session lifecycle;
- dashboard runtime integration.

The implementation preserves the canonical Node and Health vocabulary
rather than introducing parallel domain models.

---

## 4. Stream Health architecture

Stream Health evolved incrementally through:

    normalized evidence
        -> temporal Health
        -> Health transitions
        -> Events
        -> Alarm policy
        -> multiprotocol aggregation
        -> Platform Health
        -> Dashboard
        -> protocol specialization

The architecture preserves explicit separation between:

- measurement;
- Health;
- Expected Presence;
- Events;
- Alarms;
- History/Evidence;
- presentation;
- future Media/Track Health.

Observed absence is not automatically interpreted as failure.

Insufficient evidence is not promoted to HEALTHY.

---

## 5. Protocol specialization completion

The protocol sequence defined for ENG-013B is complete:

    SRT
      -> RTMP
      -> RTSP
      -> HLS
      -> WebRTC

Specialized implementation exists for all five protocol families.

The specializations reuse canonical `HealthStatus` and feed the common
multiprotocol aggregation architecture.

No independent protocol-specific NOC hierarchy was created.

---

## 6. SRT Health

SRT established the initial specialized connection Health foundation.

Its implementation includes normalized MediaMTX evidence, temporal
stabilization, degradation/recovery semantics and integration with the
common NOC architecture.

SRT physical sessions have been used throughout ENG-013B as operational
evidence.

---

## 7. RTMP Health

RTMP introduced temporal connection Health based on effective byte
progression.

The implementation preserves:

- SessionSnapshot population authority;
- specialized evidence precedence;
- conservative UNKNOWN behavior;
- separation from Expected Presence.

Physical validation demonstrated a real RTMP reader with positive
temporal traffic.

Detailed evidence:

    07-RTMP-HEALTH-EVIDENCE.md
    08-POST-BLOCK-8-STABILIZATION-EVIDENCE.md

---

## 8. RTSP Health

RTSP introduced specialized session Health without copying SRT
stabilization semantics blindly.

Physical validation established real RTSP reader behavior and outbound
traffic semantics.

Detailed evidence:

    09-RTSP-HEALTH-EVIDENCE.md

---

## 9. HLS Health

HLS preserves its demand-driven lifecycle.

With `hlsAlwaysRemux: false`, muxer presence depends on HLS demand and is
not interpreted as Expected Presence.

Physical validation against `impact` demonstrated:

- MediaMTX HLS listener;
- demand-driven muxer creation;
- real `hlsSession`;
- H264/AAC LL-HLS;
- video/audio child playlists;
- evolving LL-HLS parts and segments;
- stable muxer identity;
- advancing request timestamp;
- positive outbound counter progression.

The observed counter delta is evidence of temporal HLS traffic.

It is not presented as the encoded audiovisual bitrate because the
controlled validation did not continuously download every media part.

Detailed evidence:

    10-HLS-HEALTH-EVIDENCE.md

---

## 10. WebRTC Health

WebRTC Health uses temporal evidence according to session role.

For READER:

    bytes_sent

For PUBLISHER:

    bytes_received

Physical validation against `impact` demonstrated:

- real WebRTC reader sessions;
- established PeerConnections;
- ICE candidate evidence;
- correlation between WebRTC API sessions and path readers;
- multiple simultaneous readers;
- stable temporal session identity;
- positive server-to-reader traffic.

Inbound RTP loss/jitter fields are not interpreted as browser-side QoE
for outbound reader media without verified directional semantics.

Detailed evidence:

    11-WEBRTC-HEALTH-EVIDENCE.md

---

## 11. Multiprotocol aggregation

`StreamingHealthAggregator` combines generic observed sessions with
specialized protocol Health.

`SessionSnapshot` remains the population authority.

Specialized evidence enriches an observed session only when matching is
deterministic.

The aggregation hierarchy supports:

    connection/session
        -> protocol
        -> service
        -> platform

This prevents protocol specializations from creating duplicate
populations or parallel platform-health models.

---

## 12. Dashboard integration

`PlatformHealth` is transported through the existing dashboard
application/snapshot/service architecture.

Specialized protocol Health is projected into `CONNECTED CLIENTS`.

The dashboard preserves separation among:

- NODE HEALTH;
- STREAM HEALTH;
- PLATFORM HEALTH;
- CONNECTED CLIENTS;
- RECENT EVENTS;
- ACTIVE ALARMS.

Presentation does not become the source of Health truth.

---

## 13. Events, alarms and durable evidence

Health transitions are detected semantically once and reused by
downstream services.

Events reuse the existing Event infrastructure.

Alarm lifecycle reuses the existing Alarm infrastructure and supports
raise/keep/resolve semantics without creating alarm storms.

History/Evidence remains durable through the existing persistence
architecture.

No protocol specialization introduces a parallel event, alarm or history
subsystem.

---

## 14. Physical and operational validation

ENG-013B has been validated against the operational `ejtv-01` platform
running MediaMTX v1.19.2.

Closure audit confirmed:

- MediaMTX active;
- expected protocol listeners;
- real physical paths;
- real SRT session;
- real WebRTC sessions;
- established WebRTC PeerConnections;
- unique NOC runtime owner;
- expected History DB/WAL ownership;
- Control Center health API operational;
- IAM/JWT protection active;
- repository synchronized with origin before closure documentation.

The authenticated Dashboard correlation was not executed during the
closure audit because the existing administrator credential was not
available from bootstrap configuration.

This is recorded as a limitation of audit evidence, not as a functional
failure.

---

## 15. Automated verification

Targeted protocol verification at evidence consolidation included:

    HLS:     19 passed
    WebRTC:  21 passed

The final complete backend regression was executed after closure
documentation consolidation:

    3394 passed
    0 failed
    1 warning
    68.75 seconds
    pytest_rc=0

The remaining warning is the known Starlette/httpx TestClient
deprecation warning.

No source-code or test changes were detected after the regression.

The technical verification required before the closure commit is PASS.
Formal repository closure still requires selective staging, commit, push
and origin synchronization verification.

---

## 16. Evidence set

ENG-013B closure evidence consists of:

    01-NODE-HEALTH-FAILURE-RECOVERY-EVIDENCE.md
    02-STREAM-HEALTH-CONTRACT.md
    03-STREAM-HEALTH-TEMPORAL-EVIDENCE.md
    04-STREAM-HEALTH-ALARM-POLICY-EVIDENCE.md
    05-STREAM-HEALTH-AGGREGATION-EVIDENCE.md
    06-PLATFORM-HEALTH-DASHBOARD-EVIDENCE.md
    07-RTMP-HEALTH-EVIDENCE.md
    08-POST-BLOCK-8-STABILIZATION-EVIDENCE.md
    09-RTSP-HEALTH-EVIDENCE.md
    10-HLS-HEALTH-EVIDENCE.md
    11-WEBRTC-HEALTH-EVIDENCE.md
    12-ENG-013B-CLOSURE-EVIDENCE.md

The directory README provides the local evidence index.

The ENG-013 top-level `09-EVIDENCE.md` provides the global evidence
index.

---

## 17. Definition of Done checkpoint

Before formal closure:

    contract / invariant                 PASS
    implementation                       PASS
    targeted tests                       PASS
    related regression                   PASS
    physical validation                  PASS
    documentation                        PASS
    final full regression                PASS
    clean selective diff                 PENDING
    commit                               PENDING
    push                                 PENDING
    origin synchronization               PENDING

No ENG-014 work shall begin before the remaining closure steps complete.

---

## 18. Final closure transition

When the final backend regression passes and the documentation diff is
accepted, this evidence may transition from:

    CLOSURE CANDIDATE

to:

    CLOSED

only after:

    selective staging
        -> commit
        -> push
        -> origin synchronization verification

Runtime artifacts such as SQLite WAL/SHM files are not part of the
closure commit.
