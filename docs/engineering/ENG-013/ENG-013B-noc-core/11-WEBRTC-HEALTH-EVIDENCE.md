# ENG-013B — WebRTC Health Evidence

## 1. Scope

This document records the implementation and validation evidence for the
WebRTC Health specialization inside ENG-013B.

The specialization preserves the common Stream Health architecture while
using only WebRTC evidence whose operational meaning has been established.

The validated flow is:

    MediaMTX WebRTC session API
        -> MediaMTXSessionClient
        -> MediaMTXSessionAdapter
        -> SessionSnapshot
        -> WebRTCSessionHealthService
        -> WebRTCSessionHealth
        -> StreamingHealthAggregator
        -> PlatformHealth
        -> DashboardApplication
        -> DashboardSnapshotService
        -> DashboardService
        -> CONNECTED CLIENTS

WebRTC Health remains observed session/transport health.

It is not a general browser QoE model.

---

## 2. Architectural boundary

The current specialization uses evidence whose direction and temporal
meaning are known:

- session identity;
- path;
- role;
- state;
- connection time;
- bytes received;
- bytes sent;
- temporal counter progression;
- effective bitrate derived from that progression.

MediaMTX can expose additional WebRTC / RTP / RTCP fields.

Those fields are not automatically promoted into Health semantics merely
because they are available.

In particular, loss, jitter and RTT require evidence whose direction and
meaning correspond to the condition being evaluated.

No unsupported QoE conclusion is introduced.

---

## 3. MediaMTX WebRTC adapter

`MediaMTXSessionClient` exposes:

    /v3/webrtcsessions/list

through `get_webrtc_sessions()`.

`MediaMTXSessionAdapter` includes WebRTC observations in the generic
session snapshot and provides `get_webrtc_snapshot()`.

Observed MediaMTX WebRTC sessions are normalized into the common
`ActiveSession` model.

This preserves the protocol-independent session architecture while
allowing specialized WebRTC Health to be evaluated later.

---

## 4. WebRTC domain model

The specialized domain object is:

    WebRTCSessionHealth

It contains:

- `session_id`;
- `path_name`;
- `state`;
- `effective_delta_bytes`;
- `effective_bitrate_mbps`;
- `status`;
- `message`.

The model validates:

- non-empty session identity;
- non-empty path;
- non-empty state;
- non-empty explanatory message;
- non-negative effective byte delta;
- finite and non-negative effective bitrate.

The canonical `HealthStatus` vocabulary is reused.

No independent WebRTC status hierarchy is introduced.

---

## 5. Temporal WebRTC Health contract

`WebRTCSessionHealthService` evaluates previous and current
`SessionSnapshot` observations.

Only WebRTC sessions with an observed path are projected.

The first observation remains UNKNOWN because no temporal delta exists.

Temporal continuity requires:

- the same session identity;
- WebRTC protocol;
- the same path;
- the same role;
- the same `connected_since`;
- a strictly positive observation interval.

Traffic direction follows the observed role.

For a WebRTC READER:

    effective_delta_bytes =
        current.bytes_sent - previous.bytes_sent

For a WebRTC PUBLISHER:

    effective_delta_bytes =
        current.bytes_received - previous.bytes_received

When the effective delta is positive:

    effective_bitrate_mbps =
        effective_delta_bytes
        * 8
        / interval_seconds
        / 1_000_000

and the specialized Health becomes HEALTHY.

---

## 6. Conservative UNKNOWN behavior

The implementation does not fabricate degradation when temporal evidence
is insufficient.

The following remain UNKNOWN:

- first observation;
- zero effective traffic delta;
- counter reset;
- zero or negative temporal interval;
- session identity discontinuity;
- unknown/unsupported role.

Non-WebRTC sessions are excluded.

WebRTC observations without a path are excluded.

No arbitrary degradation threshold was introduced.

---

## 7. Multiprotocol aggregation

`StreamingHealthAggregator` accepts specialized
`WebRTCSessionHealth` evidence.

Specialized evidence is associated with a generic observed session using:

- `session_id`;
- `path`.

The specialized result is used only when exactly one matching WebRTC
Health observation exists.

Ambiguous or orphan specialized evidence is not allowed to override the
generic session evidence.

This preserves deterministic multiprotocol aggregation.

---

## 8. Dashboard runtime integration

`DashboardApplication` receives a `WebRTCSessionHealthService`.

For each temporal refresh it builds WebRTC Health from the previous and
current session snapshots.

The resulting specialized observations are supplied to the
`StreamingHealthAggregator`.

WebRTC evidence then follows the existing dashboard flow:

    PlatformHealth
        -> DashboardSnapshotInput
        -> DashboardSnapshotService
        -> DashboardService

No parallel WebRTC-only dashboard architecture was introduced.

---

## 9. CONNECTED CLIENTS projection

WebRTC specialized Health is propagated into the dashboard
`CONNECTED CLIENTS` presentation.

The presentation can therefore use the specialized WebRTC status and
effective bitrate associated with the observed client session.

Duplicate or ambiguous specialized evidence is handled conservatively.

The generic session remains the population authority.

Specialized Health enriches the observed session; it does not create a
second client population.

---

## 10. Physical WebRTC model

Physical validation was performed against MediaMTX v1.19.2 using the
`impact` service.

The validated path was:

    path: impact
    source: SRT
    video: H264
    audio: MPEG-4 Audio
    resolution: 1920x1080
    video profile: Main
    video level: 4

The path remained:

    ready: true
    available: true
    online: true

during validation.

WebRTC playback was established through the MediaMTX WebRTC/WHEP
interface.

---

## 11. Physical PeerConnection evidence

MediaMTX exposed three simultaneous WebRTC reader sessions on `impact`
during closure reconstruction.

All three observations reported:

    peerConnectionEstablished: true
    state: read
    path: impact

The sessions had distinct IDs and represented independent browser
connections.

Observed clients included Firefox on Windows and Firefox on Linux.

MediaMTX path evidence independently listed the same three session IDs as:

    type: webRTCSession

This correlates the WebRTC session API with the active reader population
of `impact`.

---

## 12. ICE / candidate evidence

The physical WebRTC API exposed ICE candidate information for established
sessions.

Observed local candidates included host/UDP candidates on MediaMTX
interfaces using the configured ICE port.

Observed remote candidates included peer-reflexive UDP candidates.

This evidence confirms that ICE candidate negotiation produced
established PeerConnections.

The current Health model does not independently score candidate type or
network path quality.

ICE evidence is therefore retained as operational evidence rather than
converted into an unsupported Health threshold.

---

## 13. Physical temporal traffic validation

Previous physical validation observed the same WebRTC reader session
across two temporal snapshots.

The reader's outbound byte counter increased by approximately 7.6 MB over
approximately 10 seconds.

The resulting effective traffic was approximately 6 Mbps.

This matches the current WebRTC READER contract:

    reader -> bytes_sent

and produced specialized:

    HealthStatus.HEALTHY

The result demonstrates observed server-to-reader WebRTC traffic.

It does not by itself prove perceptual media quality at the browser.

---

## 14. RTP loss and jitter semantic boundary

MediaMTX exposes fields including:

    inboundRTPPackets
    inboundRTPPacketsLost
    inboundRTPPacketsJitter
    outboundRTPPackets

During the observed `state=read` sessions, audiovisual RTP traffic is
sent from MediaMTX toward the browser.

The observed inbound RTP loss/jitter counters therefore must not be
interpreted automatically as browser-side loss or jitter for the
outbound media stream.

Consequently, the current WebRTC Health specialization does not use those
fields to claim:

- zero client packet loss;
- zero client jitter;
- browser QoE;
- end-to-end media quality.

Loss, jitter and RTT may be incorporated in a future specialization only
when their direction, source and operational meaning are verified.

---

## 15. Codec boundary observed during validation

Physical validation established successful WebRTC playback for `impact`,
whose video is H264.

Separate tests against services carrying H265 did not negotiate
successfully with the tested Firefox client and MediaMTX reported that
the codecs were not supported by that client.

This observation is client/test specific.

It is not generalized into a claim that WebRTC universally cannot carry
H265.

Codec compatibility remains distinct from the current temporal WebRTC
transport Health contract.

---

## 16. Automated verification

WebRTC domain and temporal service tests cover:

- preservation of observed evidence;
- blank required text rejection;
- negative delta rejection;
- invalid bitrate rejection;
- public domain export;
- first observation UNKNOWN;
- READER `bytes_sent` direction;
- PUBLISHER `bytes_received` direction;
- positive temporal delta -> HEALTHY;
- zero delta -> UNKNOWN;
- counter reset -> UNKNOWN;
- zero/negative interval -> UNKNOWN;
- identity change -> UNKNOWN;
- unknown role -> UNKNOWN;
- non-WebRTC exclusion;
- WebRTC-without-path exclusion.

At closure reconstruction time:

    21 passed

for:

    tests/domain/streaming/test_webrtc_health.py
    tests/services/test_webrtc_session_health_service.py

Additional adapter, aggregation and dashboard tests verify WebRTC
normalization and propagation through the multiprotocol architecture.

---

## 17. Implementation traceability

WebRTC specialization was introduced through:

    89d3da0 feat(streaming): add WebRTC session health

This change covered:

- MediaMTX WebRTC adapter integration;
- WebRTC domain Health;
- temporal WebRTC Health service;
- multiprotocol aggregation;
- DashboardApplication integration;
- adapter/domain/service/aggregation/dashboard tests.

Dashboard presentation was completed through:

    8eb5dc0 feat(dashboard): expose WebRTC health in connected clients

This completed propagation through:

- DashboardApplication;
- DashboardSnapshotService;
- DashboardService;
- CONNECTED CLIENTS;
- associated dashboard tests.

---

## 18. Physical validation result

Physical WebRTC validation is PASS for the current ENG-013B scope.

Demonstrated facts include:

- MediaMTX WebRTC API operational;
- real WebRTC reader sessions;
- established PeerConnections;
- ICE candidate evidence;
- active `impact` H264/AAC path;
- correlation between WebRTC API sessions and path readers;
- multiple simultaneous WebRTC readers;
- stable session identity during temporal observation;
- positive outbound reader traffic;
- effective bitrate derived from verified byte direction;
- specialized Health reaching HEALTHY;
- multiprotocol aggregation integration;
- dashboard propagation;
- targeted WebRTC regression GREEN.

The validation does not claim browser-side loss/jitter values or
perceptual QoE without corresponding evidence.

---

## 19. Closure status

WebRTC Health specialization:

- MediaMTX adapter: GREEN;
- domain contract: GREEN;
- temporal evaluation: GREEN;
- READER traffic direction: GREEN;
- PUBLISHER traffic direction: GREEN;
- conservative UNKNOWN behavior: GREEN;
- multiprotocol aggregation: GREEN;
- DashboardApplication integration: GREEN;
- Platform Health integration: GREEN;
- CONNECTED CLIENTS projection: GREEN;
- established PeerConnection evidence: GREEN;
- physical temporal traffic validation: GREEN;
- targeted automated verification: GREEN;
- semantic boundary for RTP loss/jitter: preserved.

WebRTC Health is functionally complete for the current ENG-013B scope.

No unsupported degradation threshold was introduced.

No browser QoE semantics were invented.

No Expected Presence semantics were introduced.

No Media/Track Health semantics were introduced.

With HLS and WebRTC evidence consolidated, the protocol-specialization
sequence defined for ENG-013B is complete.

ENG-013B can proceed to final multiprotocol closure verification.
