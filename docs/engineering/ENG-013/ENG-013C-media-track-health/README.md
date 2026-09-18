# ENG-013C — Media / Track Health

ENG-013C extends the EJTV NOC with media-level observation and health
semantics while preserving the nodal architecture established by
ENG-013A and the operational health infrastructure delivered by
ENG-013B.

## Objective

Observe the audiovisual media entering the platform independently from
the connection/session health already implemented by ENG-013B.

ENG-013C must be able to distinguish cases such as:

- connection healthy, media healthy;
- connection healthy, video degraded;
- connection healthy, audio degraded;
- connection healthy, container/transport evidence degraded;
- media evidence unavailable or insufficient.

## Architectural principle

Media observation is not an independent monitoring system.

Media evidence belongs to the existing:

Node -> Service -> Source

relationship and must reuse the NOC infrastructure for snapshots,
health transitions, events, alarms, history and evidence.

Terminal and Web/API views must consume the same domain/application
state. User interfaces must not independently calculate Media Health.

## Documents

### `01-DOMAIN-OBSERVATION-CONTRACT.md`

Defines the first ENG-013C domain boundary:

- InputMediaObservation
- EvidenceAvailability
- ContainerObservation
- MPEGTSObservation
- MPEGTSProgramObservation
- MPEGTSStreamObservation
- PCRObservation
- VideoTrackObservation
- AudioTrackObservation

This first contract describes observed evidence only.

Expected media profiles, Health evaluation, temporal stabilization,
events, alarms and presentation integration are intentionally deferred
to later contracts.
