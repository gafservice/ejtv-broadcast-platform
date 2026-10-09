# ENG-013 — Implementation Status

## ENG-013A — Node Contract Specification

Status:

    ARCHITECTURE FROZEN

Version:

    1.0.0

La especificación de contrato de nodo permanece congelada.

Las modificaciones del contrato deben seguir el proceso de Versioning y
ChangeLog definido por ENG-013A.

---

## ENG-013B — NOC Core

Status:

    CLOSURE CANDIDATE

ENG-013B ha completado funcionalmente el alcance actual del NOC Core.

Implementación disponible:

- Node Health;
- Node Availability;
- Node Capability;
- Node Capacity;
- Node Metric;
- Node Event;
- Node Alarm;
- Node Heartbeat;
- Node Snapshot;
- durable History/Evidence;
- Network Interface Health;
- Session lifecycle;
- Stream Health temporal;
- Health transitions;
- Events integration;
- Alarm lifecycle integration;
- multiprotocol Stream Health aggregation;
- Platform Health;
- Dashboard integration;
- SRT Health;
- RTMP Health;
- RTSP Health;
- HLS Health;
- WebRTC Health;
- CONNECTED CLIENTS Health projection.

La especialización multiprotocolo definida para ENG-013B está completa:

    SRT -> RTMP -> RTSP -> HLS -> WebRTC

Las validaciones físicas documentadas incluyen Node Health,
SRT/RTMP/RTSP, LL-HLS y WebRTC.

La auditoría operacional confirmó además:

- MediaMTX operativo;
- runtime owner único;
- History DB/WAL asociado al runtime esperado;
- API health operativa;
- protección IAM/JWT activa;
- sesiones físicas SRT y WebRTC;
- paths físicos coherentes con MediaMTX.

La correlación autenticada del Dashboard no fue ejecutada durante la
auditoría de cierre porque la credencial del administrador existente no
estaba disponible en bootstrap configuration. Esto se registra como una
limitación de evidencia y no como una falla funcional.

La regresión completa final de cierre fue ejecutada después de consolidar
la documentación:

    3394 passed
    0 failed
    1 warning
    68.75 seconds
    pytest_rc=0

El warning corresponde a la deprecación conocida de Starlette/httpx
TestClient.

No se detectaron cambios de código fuente ni tests después de la
regresión.

Pendiente para cierre formal:

1. revisión final del diff documental;
2. staging selectivo;
3. commit;
4. push;
5. verificación local/origin.

ENG-014 permanece fuera de alcance hasta completar estos pasos.


---

## ENG-013C — Current Engineering Checkpoint

### Reference

- Date: 2026-10-09
- Project: Enlace Broadcast Platform
- Branch: `eng-013c-media-track-health`
- Last completed block: `235E.25`
- Functionality: INCOMING Row Selection / Navigation
- Functional commit: `2ec9590cb79d42fb0d190ec2c1d482839e3667c0`
- Parent commit: `66abcbcefff1e594a64cf35d2290fd0e6edbf028`
- Remote: `origin`
- Push: VERIFIED
- Local/remote synchronization: GREEN

### Acceptance evidence

- Targeted regression: 109 passed.
- Physical visual validation: EJTV, ENLACE, IMPACT.
- Committed files: 10.
- Staged diff integrity: GREEN.
- Force push: not used.
- Services restarted during commit/push: no.

### Current state

`235E.25 — CLOSED / GREEN`

### Next authorized block

`235E.26 — INCOMING Signal Detail`

Status: NOT STARTED.

### Checkpoint management rule

Every functional push must be followed by a verified
documentation checkpoint before beginning the next block.

Functional commits and documentation commits are tracked
separately.

Historical documentation must be preserved unless a
specific correction is supported by Git evidence.
