# ENG-013C — Domain Observation Contract

## 1. Purpose

This document defines the first domain contract for ENG-013C Media /
Track Health.

The contract represents evidence observed from multimedia input without
assigning a Health conclusion to that evidence.

The fundamental separation is:

Observation != Expectation != Health

An observation describes what was measured or discovered.

An expectation describes what should exist or how it should behave.

Health is the result of evaluating evidence against intrinsic integrity
rules and/or explicit expectations.

These responsibilities must remain separate.

---

## 2. Architectural boundary

ENG-013C remains part of the existing nodal NOC architecture.

Conceptually:

    Node
      |
      +-- NodeInstance
            |
            +-- Service
                  |
                  +-- Source
                        |
                        +-- InputMediaObservation

InputMediaObservation does not own a separate event store, alarm store,
history database or dashboard state.

Future ENG-013C integration must reuse the existing NOC mechanisms for:

- Node snapshots;
- Health transitions;
- Node events;
- Node alarms;
- durable history;
- operational evidence;
- terminal presentation;
- Web/API presentation.

The NOC domain/application state remains the source of truth.

---

## 3. Scope of Contract 1

Contract 1 defines observation-domain concepts only:

- EvidenceAvailability;
- InputMediaObservation;
- ContainerObservation;
- MPEGTSObservation;
- MPEGTSProgramObservation;
- MPEGTSStreamObservation;
- PCRObservation;
- VideoTrackObservation;
- AudioTrackObservation.

It defines identity, evidence boundaries and invariants.

It does not classify Health.

---

## 4. Explicitly outside Contract 1

The following concepts are intentionally deferred:

- ExpectedMediaProfile;
- required/optional track policy;
- expected codecs;
- expected resolution;
- expected frame rate;
- expected bitrate;
- expected GOP;
- expected MPEG-TS program or PID topology;
- HEALTHY / DEGRADED / CRITICAL classification;
- Health aggregation;
- temporal stabilization;
- Health transitions;
- event generation;
- alarm policy;
- dashboard integration;
- Web/API integration;
- failure-origin inference;
- learned baselines;
- arbitrary operational thresholds.

Contract 1 must not introduce such behavior indirectly.

---

## 5. Identity

One InputMediaObservation belongs to one operational observation scope.

The canonical scope consists of:

- node_id;
- instance_id;
- service_id;
- path_name;
- source identity when available;
- observed_at.

### 5.1 node_id

`node_id` identifies the logical NOC Node.

The canonical existing `NodeId` domain type must be reused.

### 5.2 instance_id

`instance_id` identifies the concrete operational Node instance.

The canonical existing `NodeInstanceId` type must be reused.

This prevents evidence captured by different executions of the same
logical Node from being silently mixed.

### 5.3 service_id

`service_id` identifies the logical multimedia service.

Contract 1 preserves the current repository convention:

    service_id: str

The value must be normalized and must not be blank.

Contract 1 does not introduce a new ServiceId value object.

### 5.4 path_name

`path_name` identifies the MediaMTX path or equivalent normalized media
path associated with the observation.

It must not be blank when present.

Path identity and source identity are separate concepts.

### 5.5 source identity

Source identity describes the observed upstream source when such
evidence is available.

Contract 1 does not require one transport-specific representation.

Source IP, transport session identity or similar evidence must not be
confused with `service_id` or `path_name`.

A later capture/adapter contract may specialize source evidence.

### 5.6 observed_at

`observed_at` is the timestamp of the observation.

It must:

- be a datetime;
- be timezone-aware;
- be expressed in UTC.

Naive datetimes are invalid.

Timezone-aware non-UTC datetimes are invalid.

This follows the strict time invariant already established by the NOC
Node contract.

---

## 6. Evidence availability

Evidence availability is independent from Health.

Contract 1 requires an `EvidenceAvailability` concept capable of
distinguishing at least:

- AVAILABLE
- UNAVAILABLE
- INSUFFICIENT
- NOT_APPLICABLE

### AVAILABLE

The observer successfully produced evidence for the corresponding
observation scope.

### UNAVAILABLE

Evidence could not be obtained.

Examples include observer execution failure or inaccessible input.

UNAVAILABLE does not mean the media itself is unhealthy.

### INSUFFICIENT

Some evidence exists, but it is insufficient for the intended
interpretation.

Examples include an observation window too short for a temporal
measurement.

INSUFFICIENT does not mean the media itself is unhealthy.

### NOT_APPLICABLE

The evidence category does not apply to the observed media.

Example:

MPEG-TS evidence is NOT_APPLICABLE to an input that does not use an
MPEG-TS container.

`HealthStatus.UNKNOWN` must not be reused as evidence availability.

---

## 7. InputMediaObservation

`InputMediaObservation` is the aggregate observation for one multimedia
input at one observation instant.

Conceptually:

    InputMediaObservation
      |
      +-- identity
      |
      +-- container
      |
      +-- video
      |
      +-- audio

Minimum conceptual fields:

    node_id: NodeId
    instance_id: NodeInstanceId
    service_id: str
    path_name: str | None
    source: source evidence | None
    observed_at: datetime
    container: ContainerObservation | None
    video: VideoTrackObservation | None
    audio: AudioTrackObservation | None

The object contains evidence only.

It must not contain:

- HealthStatus;
- expected values;
- thresholds;
- alarm state;
- event state.

Absence of `video` or `audio` is not itself a failure.

Track requirements belong to ExpectedMediaProfile, not to the raw
observation.

---

## 8. ContainerObservation

`ContainerObservation` represents container-level evidence without
assuming one specific container technology.

Minimum conceptual responsibilities:

    container_type
    availability
    mpegts

`container_type` is descriptive evidence.

Examples may include MPEG-TS or another future normalized container
identifier.

The generic container object must not expose MPEG-TS-specific fields
such as PAT, PMT, PID, PCR or continuity counter directly.

MPEG-TS-specific evidence belongs to `MPEGTSObservation`.

---

## 9. MPEGTSObservation

`MPEGTSObservation` represents MPEG-TS-specific evidence.

It is optional and applicable only when MPEG-TS evidence is available
for the observed input.

The contract is based on physical ENG-013C inspections performed
against real EJTV and ENLACE UDP/MPEG-TS input traffic.

The following categories are supported.

### 9.1 Transport integrity evidence

Observed evidence may include:

    transport_packet_count
    sync_error_count
    malformed_packet_count
    transport_error_indicator_count
    continuity_check_count
    continuity_error_count
    discontinuity_indicator_count

These values are observations.

They are not themselves HealthStatus values.

Counts must not be negative.

A continuity error count must not exceed the corresponding number of
continuity checks.

### 9.2 Program structure

Program topology must be represented structurally rather than by
hard-coded EJTV PID values.

Conceptually:

    MPEGTSProgramObservation
      program_number
      pmt_pid
      pcr_pid
      streams

An MPEG-TS observation may contain one or more observed programs.

Contract 1 must not assume:

- program number 1;
- PMT PID 0x0100;
- PCR PID 0x002d;
- video PID 0x0103;
- audio PID 0x0104.

Those values were physical observations, not universal requirements.

### 9.3 Elementary streams

Elementary streams must be represented as observations.

Conceptually:

    MPEGTSStreamObservation
      pid
      stream_type

Optional normalized codec/media-kind information may be added only
when it is directly supported by observed evidence.

PID values must be valid MPEG-TS PID values.

Contract 1 does not classify a PID change as unhealthy.

Expected PID topology belongs to a future ExpectedMediaProfile.

### 9.4 PAT / PMT evidence

The observation may preserve evidence including:

- transport_stream_id;
- PAT presence;
- PAT version;
- program number;
- PMT PID;
- PMT presence;
- PMT version;
- PCR PID;
- elementary stream PID;
- elementary stream type.

PAT/PMT presence is descriptive evidence in Contract 1.

Expected topology and persistence semantics belong to later evaluation
contracts.

---

## 10. PCRObservation

PCR evidence is temporal container evidence.

Conceptually it may include:

    availability
    pid
    sample_count
    first_pcr
    last_pcr
    pcr_span
    minimum_delta
    maximum_delta
    average_delta
    median_delta

`PCRObservation` represents sender-PCR clock evidence.

Local packet-arrival timing is a distinct observation domain and must
not be collapsed into PCR progression. Therefore local arrival-gap
statistics, local arrival span and derived PCR-versus-arrival span
differences are intentionally deferred from the first PCR slice.

For MPEG-TS program topology, PCR evidence belongs to the observed
program that declares the corresponding `pcr_pid`. This preserves
correct semantics for transport streams containing more than one
program.

Only evidence actually produced by the observer may be populated.

PCR values and deltas must not be assigned arbitrary Health thresholds
by Contract 1.

The following must not be interpreted directly as Health:

- absolute PCR value;
- absolute PCR origin;
- one local arrival-time variation;
- difference between capture clock and sender clock without an
  evaluation policy.

Future implementation must account for MPEG-TS PCR wrap semantics
before using long-running PCR progression operationally.

---

## 11. VideoTrackObservation

`VideoTrackObservation` represents observed video-track evidence.

It is independent from AudioTrackObservation.

The first implemented video-track slice may preserve descriptive
evidence including:

    availability
    codec
    profile
    level
    width
    height
    frame_rate
    gop

Additional candidate evidence remains valid for later observation
slices, including:

    bitrate
    packet_count
    frame_count
    keyframe_count
    first_timestamp
    last_timestamp
    observed_span
    maximum_packet_gap

Fields unavailable from a given observer may remain absent according to
the implementation representation.

### 11.1 Frame-rate evidence

Frame rate is descriptive evidence.

When an observer provides frame rate as a rational value, the domain
must preserve that rational representation without requiring an
imprecise floating-point conversion.

Conceptually:

    FrameRateObservation
      numerator
      denominator

Both values are integers.

The numerator must not be negative.

The denominator must be strictly positive.

Contract 1 does not define an expected frame rate or tolerance.

For example, an observed value of `30000/1001` is evidence only. It is
not inherently healthy or unhealthy.

### 11.2 GOPObservation

GOP / keyframe evidence is represented separately from generic
video-track metadata.

Conceptually:

    GOPObservation
      availability
      observed_frame_count
      keyframe_count
      i_frame_count
      p_frame_count
      b_frame_count
      interval_count
      minimum_interval
      maximum_interval
      average_interval
      median_interval
      minimum_frames_per_interval
      maximum_frames_per_interval
      average_frames_per_interval
      median_frames_per_interval

`GOPObservation` contains observed evidence only.

Counts must not be negative.

When interval statistics are present, temporal values must not be
negative.

When both minimum and maximum interval values are present, minimum must
not exceed maximum.

Average and median interval values, when present together with minimum
or maximum evidence, must remain within the observed range.

Frames-per-interval evidence follows the same intrinsic ordering
principle.

The observation does not define an `outlier` concept. Determining
whether an interval is exceptional requires an evaluation policy or
expected profile.

The observation also does not equate an ffprobe-reported key frame with
a codec-specific random-access type such as HEVC IDR or CRA unless a
future observer provides that deeper bitstream evidence explicitly.

### 11.3 Physical evidence boundary

Physical ENG-013C inspections against real ENLACE and EJTV inputs
demonstrated that GOP evidence cannot be reduced to one configured or
assumed duration.

Observed evidence included predominantly approximately 2.002-second,
60-frame keyframe intervals, while separate ENLACE observation windows
also contained longer reported-keyframe intervals.

Those measurements justify preserving interval distribution evidence.

They do not establish:

- an expected GOP duration;
- an acceptable GOP tolerance;
- whether a longer interval is unhealthy;
- whether B-frames are required or forbidden;
- whether two services must use the same GOP structure;
- whether every reported key frame is an HEVC IDR.

Those conclusions belong to ExpectedMediaProfile and later evaluation
contracts.

### 11.4 Health boundary

Contract 1 does not define acceptable values for video-track evidence.

In particular:

- H.264 is not inherently healthy;
- H.265 is not inherently healthy;
- 1920x1080 is not inherently healthy;
- 30 fps is not inherently healthy;
- 6 Mbps is not inherently healthy;
- a 2 second GOP is not inherently healthy;
- a 4 or 6 second observed keyframe interval is not inherently
  unhealthy.

Such interpretations require an expected profile or later evaluation
contract.


## 12. AudioTrackObservation

`AudioTrackObservation` represents observed audio-track evidence.

It is independent from `VideoTrackObservation`.

The first implemented audio-track slice may preserve descriptive
evidence including:

    availability
    codec
    profile
    sample_rate
    channels
    channel_layout

Descriptive string evidence must not be blank when present.

`sample_rate` and `channels`, when present, must be strictly positive
integers.

Fields unavailable from a given observer may remain absent. Availability
does not require every optional descriptive field to be populated.

Additional candidate evidence remains valid for later observation
slices, including:

    bitrate
    packet_count
    first_timestamp
    last_timestamp
    observed_span
    maximum_packet_gap

Contract 1 does not define acceptable audio codec, profile, bitrate,
sample rate, channel count, channel layout or temporal threshold.

For example, observed AAC LC, 48000 Hz, two-channel stereo evidence is
descriptive evidence only. It is not inherently healthy or unhealthy.

An absent `AudioTrackObservation` does not by itself mean failure.

Whether audio is required, which codec is expected, or which audio
parameters are acceptable belongs to `ExpectedMediaProfile` and later
evaluation contracts.

---

## 13. Observation versus expectation

The following example is valid:

    Observation:
        video.codec = H265
        video.width = 1920
        video.height = 1080

    ExpectedMediaProfile:
        video required
        codec expected = H265
        resolution expected = 1920x1080

    Evaluator:
        compares observation with expectation

    Result:
        VideoTrackHealth

The observation must not perform the comparison itself.

ExpectedMediaProfile is intentionally outside Contract 1.

---

## 14. Observation versus intrinsic integrity evidence

Some transport evidence represents an observed protocol condition
without requiring a customer-specific expected profile.

Examples include:

- invalid MPEG-TS synchronization;
- transport_error_indicator observed;
- malformed MPEG-TS packet;
- invalid continuity progression.

However, Contract 1 records only the evidence.

The mapping from such evidence to:

- HEALTHY;
- DEGRADED;
- CRITICAL;

and any persistence/severity semantics belong to a later Health
evaluation contract.

This prevents Contract 1 from silently introducing unvalidated
thresholds.

---

## 15. Missing evidence

The contract must preserve the distinction:

    NO EVIDENCE != BAD EVIDENCE

Examples:

    observer failed
        -> evidence UNAVAILABLE

    temporal window insufficient
        -> evidence INSUFFICIENT

    non-MPEG-TS input
        -> MPEG-TS evidence NOT_APPLICABLE

    observer succeeded and measured TEI
        -> evidence AVAILABLE with TEI observations

Only a later evaluator may convert the available evidence into Health.

---

## 16. Track presence

Raw observation and expected presence are separate.

Therefore:

    video = None

means that no video observation is represented.

It does not mean:

    video required but missing

Likewise:

    audio = None

does not mean an audio failure.

Future ExpectedMediaProfile policy must define whether a track is:

- required;
- optional;
- or otherwise constrained.

---

## 17. Observer independence

The domain contract must not depend directly on:

- ffprobe;
- ffmpeg;
- tshark;
- tcpdump;
- MediaMTX API implementation details.

Those are evidence producers/adapters.

The domain receives normalized evidence.

This allows future observers or capture technologies to populate the
same contract without changing Health semantics.

---

## 18. Container independence

InputMediaObservation must remain valid for non-MPEG-TS inputs.

Therefore this is forbidden:

    InputMediaObservation
        pat
        pmt
        pcr
        continuity_counter

The required structure is conceptually:

    InputMediaObservation
        |
        +-- ContainerObservation
                |
                +-- MPEGTSObservation | None

Future container-specific observations may be added without changing
the top-level media observation contract.

---

## 19. Nodal ownership

Media observation must preserve its association with the NOC Node and
NodeInstance.

ENG-013C must not create:

- a parallel Media event system;
- a parallel Media alarm system;
- a parallel Media history database;
- a separate terminal Health calculation;
- a separate Web Health calculation.

Future MediaHealth results must enter the existing NOC operational
pipeline.

---

## 20. Immutability

Observation-domain objects should follow the existing repository
pattern of immutable value-like domain records.

The intended implementation pattern is:

    @dataclass(frozen=True, slots=True)

unless a later implementation constraint demonstrates a concrete need
for another representation.

---

## 21. Validation principles

Contract 1 requires at minimum:

- NodeId type validation;
- NodeInstanceId type validation;
- non-blank normalized service_id;
- non-blank path_name when present;
- UTC-aware observed_at;
- non-negative counters;
- valid MPEG-TS PID range;
- coherent continuity counts;
- immutable observation objects;
- no HealthStatus inside observation objects;
- no expected values inside observation objects.

Cross-field validation must reject structurally impossible evidence
rather than silently normalizing it into plausible values.

---

## 22. Physical evidence behind the contract

The contract is informed by ENG-013C physical inspections including:

- MediaMTX track normalization;
- H.264 video observation;
- H.265 video observation;
- audio packet observation;
- controlled IMPACT CBR OFF/ON observation;
- real UDP/MPEG-TS capture;
- MPEG-TS dissector validation;
- PAT/PMT topology inspection;
- independent 188-byte TS packet parsing;
- continuity-counter verification;
- PCR temporal verification.

These inspections established that:

- connection/session Health and media evidence are different concerns;
- MPEG-TS topology must not be hard-coded from one service;
- packet arrival timing and sender PCR timing are different evidence;
- short observation bitrate must not become an arbitrary threshold;
- observer/dissector behavior must be validated before evidence is
  promoted into operational Health.

---

## 23. Contract 1 acceptance conditions

Contract 1 is ready for implementation tests when the following are
accepted:

1. InputMediaObservation is nodally scoped.
2. Observation is separate from expectation and Health.
3. service_id remains the existing validated string convention.
4. path and source identities remain distinct.
5. observed_at requires UTC.
6. evidence availability is separate from HealthStatus.
7. the top-level observation is container-neutral.
8. MPEG-TS evidence is represented by a specialization.
9. video and audio observations remain independent.
10. missing tracks do not imply failure.
11. no arbitrary operational thresholds exist.
12. no event/alarm/history subsystem is duplicated.
13. observer implementation details do not leak into the domain.
14. ExpectedMediaProfile and Health evaluation remain outside
    Contract 1.

---

## 24. Next step

After review and acceptance of this document, ENG-013C proceeds to:

    CONTRACT
       |
       v
    TEST RED
       |
       v
    SMALL DOMAIN CHANGE
       |
       v
    GREEN
       |
       v
    REGRESSION

No production implementation should precede the Contract 1 acceptance.
