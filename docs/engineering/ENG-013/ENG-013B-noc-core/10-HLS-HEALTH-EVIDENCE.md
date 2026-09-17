# ENG-013B — HLS Health Evidence

## 1. Scope

This document records the implementation and validation evidence for the
HLS Health specialization inside ENG-013B.

The specialization follows the common Stream Health architecture while
preserving the particular semantics of HLS. HLS is not modeled as if it
were a persistent transport connection equivalent to SRT.

The validated flow is:

    MediaMTX HLS observation
        -> MediaMTXSessionAdapter
        -> SessionSnapshot
        -> HLSSessionHealthService
        -> HLSSessionHealth
        -> StreamingHealthAggregator
        -> PlatformHealth
        -> DashboardApplication
        -> DashboardSnapshotService
        -> DashboardService
        -> CONNECTED CLIENTS

The implementation does not introduce HLS-specific alarm, event or
history subsystems.

---

## 2. Architectural boundary

HLS Health represents observed session/transport activity.

It does not claim to determine:

- Expected Presence;
- video structural health;
- GOP or IDR correctness;
- decoder compatibility;
- perceptual media quality;
- end-user QoE;
- CDN availability;
- packet-loss semantics not exposed by the current evidence.

Absence of an HLS session is not fabricated as CRITICAL.

Conditions without sufficient temporal evidence remain UNKNOWN.

---

## 3. HLS domain model

The specialized domain object is:

    HLSSessionHealth

It contains:

- `session_id`;
- `path_name`;
- `state`;
- `effective_delta_bytes`;
- `effective_bitrate_mbps`;
- `status`;
- `message`.

The domain validates:

- non-empty session identity;
- non-empty path;
- non-empty state;
- non-empty explanatory message;
- non-negative effective byte delta;
- finite and non-negative effective bitrate.

The canonical `HealthStatus` is reused.

No parallel HLS-specific status vocabulary is introduced.

---

## 4. Temporal HLS Health contract

`HLSSessionHealthService` evaluates two `SessionSnapshot` observations.

Only observed HLS sessions with a path are projected.

The first observation is UNKNOWN because no temporal delta exists yet.

Temporal continuity requires:

- the same session identity;
- HLS protocol;
- the same path;
- the same role;
- the same `connected_since`;
- a strictly positive observation interval.

For an HLS READER, effective traffic is derived from:

    current.bytes_sent - previous.bytes_sent

When the delta is positive:

    effective_delta_bytes = delta

    effective_bitrate_mbps =
        delta * 8 / interval_seconds / 1_000_000

and the specialized Health becomes HEALTHY.

The following conditions do not fabricate degradation:

- first observation;
- zero effective delta;
- counter reset;
- invalid or non-positive temporal interval;
- identity change;
- unsupported/non-reader role.

They remain UNKNOWN under the current contract.

No HLS degradation threshold was invented.

---

## 5. HLS-specific semantics

The ENG-013B Stream Health contract requires HLS to preserve its
particular lifecycle and not to be forced into the semantics of a
persistent SRT connection.

Physical validation confirmed this distinction.

With:

    hlsAlwaysRemux: false

MediaMTX did not expose an HLS muxer before HLS demand existed.

A request for the `impact` HLS master playlist created the muxer
dynamically.

Therefore the presence and lifecycle of the HLS observation are
demand-driven and must not be interpreted as Expected Presence.

---

## 6. MediaMTX physical model

Physical validation was performed against MediaMTX v1.19.2.

Relevant HLS configuration observed:

    hls: true
    hlsAddress: :8888
    hlsEncryption: false
    hlsAlwaysRemux: false
    hlsVariant: lowLatency
    hlsSegmentCount: 7
    hlsSegmentDuration: 1s
    hlsPartDuration: 200ms
    hlsDirectory: ""
    hlsMuxerCloseAfter: 60s

The validated service was:

    path: impact
    source: SRT
    video: H264
    audio: MPEG-4 Audio
    resolution: 1920x1080
    video profile: Main
    video level: 4

The source remained ready, available and online during validation.

---

## 7. LL-HLS playlist validation

The `impact` master playlist was successfully obtained through MediaMTX.

It advertised:

- H264 / AVC video;
- AAC audio;
- 1920x1080 resolution;
- 30 fps;
- separate video and audio child playlists.

The child playlists demonstrated active Low-Latency HLS generation.

Observed HLS structures included:

- `EXT-X-SERVER-CONTROL`;
- `EXT-X-PART-INF`;
- `EXT-X-MAP`;
- `EXT-X-PART`;
- `EXTINF`;
- `EXT-X-PRELOAD-HINT`;
- fragmented MP4 initialization resources;
- fragmented MP4 media parts and segments.

The playlists evolved during the physical observation.

The media sequence advanced from 1 to 3 and new video/audio parts and
segments became available.

This confirms continuing LL-HLS generation for the observed `impact`
service.

---

## 8. Physical HLS session evidence

MediaMTX exposed a real HLS reader on `impact`:

    reader type: hlsSession

The HLS reader coexisted with WebRTC readers on the same service without
requiring a MediaMTX restart or configuration change.

The HLS muxer remained the same observed instance across the temporal
measurement:

    path A: impact
    path B: impact

    created A:
        2026-09-17T12:15:36.998660569-06:00

    created B:
        2026-09-17T12:15:36.998660569-06:00

Its request timestamp progressed:

    lastRequest A:
        2026-09-17T12:15:45.681043591-06:00

    lastRequest B:
        2026-09-17T12:15:55.820906234-06:00

MediaMTX counters also progressed:

    outboundBytes A: 6910
    outboundBytes B: 14860

    bytesSent A: 6910
    bytesSent B: 14860

    delta: +7950 bytes

This is positive temporal traffic evidence and satisfies the current
specialized HLS Health contract for observed activity.

---

## 9. Bitrate interpretation boundary

The physical validation deliberately requested master and child
playlists to establish and observe HLS lifecycle and temporal counter
progression.

It did not continuously download all LL-HLS media parts and segments.

Therefore the approximately 0.00636 Mbps derived from the 7950-byte
counter delta is not interpreted as the audiovisual bitrate of
`impact`.

It represents only the traffic generated by the controlled requests
performed during this validation.

The value is useful as proof of positive temporal progression, not as a
measurement of the encoded media bitrate.

This distinction prevents the NOC from presenting unsupported QoE or
media-throughput conclusions.

---

## 10. Aggregation and runtime integration

HLS specialized Health is integrated into the existing
`StreamingHealthAggregator`.

The specialized evidence is associated with the observed session rather
than replacing the population authority of `SessionSnapshot`.

`DashboardApplication` builds HLS Health from previous/current temporal
snapshots and supplies it to the multiprotocol aggregation flow.

The resulting `PlatformHealth` continues to use the common canonical
Health architecture.

No HLS-only aggregation hierarchy was introduced.

---

## 11. Dashboard projection

HLS specialized Health is transported through:

    DashboardApplication
        -> DashboardSnapshotInput
        -> DashboardSnapshotService
        -> DashboardService

The specialized HLS evidence can therefore be projected into
`CONNECTED CLIENTS`.

The presentation preserves the separation between:

- raw/current session measurement;
- specialized protocol Health;
- Platform Health;
- Node Health;
- Events;
- Alarms;
- History/Evidence.

---

## 12. Adapter outbound-byte correction

During HLS implementation, the MediaMTX session adapter was corrected
to map HLS outbound traffic into the generic session measurement.

This is required because an HLS reader consumes outbound traffic from
the server.

The correction is covered by adapter tests and prevents the specialized
HLS temporal service from evaluating the wrong traffic direction.

---

## 13. Automated verification

The specialized HLS domain and temporal service tests cover:

- domain text normalization;
- invalid textual evidence rejection;
- invalid numeric evidence rejection;
- public domain export;
- first observation UNKNOWN;
- READER `bytes_sent` delta;
- positive delta -> HEALTHY;
- zero delta -> UNKNOWN;
- counter reset -> UNKNOWN;
- zero/negative interval -> UNKNOWN;
- identity change -> UNKNOWN;
- unsupported role -> UNKNOWN;
- non-HLS session exclusion;
- HLS-without-path exclusion.

At closure reconstruction time:

    19 passed

for:

    tests/domain/streaming/test_hls_health.py
    tests/services/test_hls_session_health_service.py

The implementation was developed incrementally through commits covering:

- HLS session health specialization;
- HLS aggregation;
- HLS runtime integration;
- HLS outbound-byte mapping;
- Dashboard / CONNECTED CLIENTS projection.

---

## 14. Physical validation result

Physical HLS validation is PASS for the current ENG-013B scope.

Demonstrated facts:

- MediaMTX HLS listener operational;
- demand-driven HLS muxer creation;
- real `hlsSession` on `impact`;
- H264/AAC LL-HLS master playlist;
- video and audio child playlists;
- continuing LL-HLS playlist evolution;
- stable muxer identity across observations;
- advancing `lastRequest`;
- positive `bytesSent` / `outboundBytes` delta;
- coexistence with WebRTC readers;
- no MediaMTX configuration modification required;
- targeted HLS regression remains GREEN.

The validation does not claim continuous media-segment throughput,
end-user QoE or media structural correctness.

Those concerns remain outside the current HLS Stream Health contract.

---

## 15. Closure status

HLS Health specialization:

- domain contract: GREEN;
- temporal evaluation: GREEN;
- HLS-specific lifecycle semantics: GREEN;
- outbound traffic direction: GREEN;
- multiprotocol aggregation: GREEN;
- DashboardApplication integration: GREEN;
- Platform Health integration: GREEN;
- CONNECTED CLIENTS projection: GREEN;
- targeted automated verification: GREEN;
- LL-HLS physical generation: GREEN;
- physical HLS session validation: GREEN;
- temporal counter progression: GREEN.

HLS Health is functionally complete for the current ENG-013B scope.

No unsupported degradation threshold was introduced.

No Expected Presence semantics were introduced.

No Media/Track Health semantics were introduced.

ENG-013B remains active pending WebRTC evidence consolidation and final
multiprotocol closure.
