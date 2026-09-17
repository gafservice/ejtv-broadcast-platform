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
