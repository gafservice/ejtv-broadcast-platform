# CHANGELOG

Todos los cambios relevantes realizados sobre la plataforma EJTV Broadcast Platform se registran en este documento siguiendo un criterio cronológico.

---

# 2026-06-30 — MISSION-012

## Tipo

Nueva funcionalidad.

---

## Resumen

Se implementó y validó el protocolo **Real-Time Messaging Protocol (RTMP)** como mecanismo oficial de contribución (ingest) para la plataforma EJTV Broadcast Platform mediante MediaMTX.

La implementación permite publicar y consumir flujos multimedia utilizando RTMP sobre TCP, integrándose con la arquitectura multimedia existente sin afectar los servicios previamente implementados.

---

## Implementación

Se verificó y habilitó la configuración correspondiente al servicio RTMP en MediaMTX.

Configuración utilizada:

```yaml
rtmp: true

rtmpAddress: :1935

rtmpEncryption: "no"
```

Durante esta misión no fue necesario modificar la configuración base distribuida por MediaMTX.

---

## Infraestructura

Se confirmó el correcto funcionamiento de:

- Ubuntu Server 24.04.4 LTS.
- MediaMTX v1.19.0.
- FFmpeg 6.1.1.
- FFprobe.
- UFW.

No fue necesario instalar componentes adicionales.

---

## Firewall

Se incorporó la regla oficial para el servicio RTMP:

```text
1935/tcp
```

La regla quedó habilitada tanto para IPv4 como para IPv6.

---

## Validación técnica

Se verificó satisfactoriamente:

- disponibilidad del listener TCP 1935;
- publicación de un flujo mediante FFmpeg;
- creación automática del stream `live/test`;
- lectura del flujo mediante FFprobe;
- reproducción mediante FFplay;
- detección de video H.264;
- detección de audio AAC;
- registro de conexiones RTMP en MediaMTX;
- cierre correcto de las sesiones al finalizar las pruebas.

---

## Integración

Se confirmó la correcta integración del protocolo RTMP con la arquitectura multimedia existente.

El flujo publicado mediante RTMP quedó disponible para redistribución mediante:

- RTSP;
- HLS;
- WebRTC;
- SRT;
- MoQ.

No fue necesaria ninguna recodificación por parte de MediaMTX.

---

## Scripts incorporados

Se creó:

```text
scripts/maintenance/rtmp-status.sh
```

El script verifica automáticamente:

- estado del servicio MediaMTX;
- configuración RTMP;
- listener TCP;
- reglas del firewall;
- soporte RTMP de FFmpeg;
- eventos recientes registrados por MediaMTX.

---

## Documentación incorporada

Se agregó la documentación técnica correspondiente:

- `docs/services/rtmp.md`

Se incorporó el procedimiento oficial de validación:

- `tests/acceptance/mission-012-rtmp.md`

Se generó la línea base:

- `docs/baseline/BASELINE-012-RTMP.md`

---

## Compatibilidad

Se confirmó compatibilidad completa con los servicios previamente implementados:

- RTSP
- HLS
- WebRTC
- SRT
- MoQ

No se detectaron regresiones durante las pruebas realizadas.

---

## Incidentes

No se registraron incidentes durante la implementación ni durante las pruebas funcionales.

---

## Estado de la misión

**MISSION-012 finalizada satisfactoriamente.**

La plataforma incorpora soporte operativo para Real-Time Messaging Protocol (RTMP), completamente validado e integrado dentro de la arquitectura EJTV Broadcast Platform.