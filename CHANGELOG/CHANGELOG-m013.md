# CHANGELOG

Todos los cambios relevantes realizados sobre la plataforma EJTV Broadcast Platform se registran en este documento siguiendo un criterio cronológico.

---

# 2026-06-30 — MISSION-013

## Tipo

Nueva funcionalidad.

---

## Resumen

Se implementó y validó el protocolo **Secure Reliable Transport (SRT)** como mecanismo oficial de contribución (ingest) para la plataforma EJTV Broadcast Platform mediante MediaMTX.

La implementación permite publicar y consumir flujos multimedia utilizando el protocolo SRT sobre UDP, manteniendo compatibilidad con el resto de la arquitectura multimedia de la plataforma.

---

## Implementación

Se verificó la configuración nativa de MediaMTX correspondiente al servicio SRT.

Configuración utilizada:

```yaml
srt: true

srtAddress: :8890
```

Durante esta misión no fue necesario modificar la configuración distribuida por MediaMTX.

Se confirmó la disponibilidad de los parámetros:

- srtReadPassphrase
- srtPublishPassphrase

Los mecanismos de autenticación permanecen deshabilitados para esta etapa del proyecto.

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

Se incorporó la regla oficial para el servicio SRT:

```text
8890/udp
```

La regla quedó habilitada tanto para IPv4 como para IPv6.

---

## Validación técnica

Se verificó satisfactoriamente:

- disponibilidad del listener UDP 8890;
- publicación de un flujo mediante FFmpeg;
- creación automática del stream `live/test`;
- lectura del flujo mediante FFprobe;
- detección de video H.264;
- detección de audio AAC;
- registro de conexiones SRT en MediaMTX;
- cierre correcto de las sesiones al finalizar las pruebas.

---

## Integración

Se confirmó la correcta integración del protocolo SRT con la arquitectura multimedia existente.

El flujo publicado mediante SRT quedó disponible para redistribución por MediaMTX sin afectar los protocolos previamente implementados.

---

## Scripts incorporados

Se creó:

```text
scripts/maintenance/srt-status.sh
```

El script verifica automáticamente:

- estado del servicio MediaMTX;
- configuración SRT;
- listener UDP;
- reglas del firewall;
- soporte SRT de FFmpeg;
- eventos recientes registrados por MediaMTX.

---

## Documentación incorporada

Se agregó la documentación técnica correspondiente:

- docs/services/srt.md

Se incorporó el procedimiento oficial de validación:

- tests/acceptance/mission-013-srt.md

Se generó la línea base:

- docs/baseline/BASELINE-013-SRT.md

---

## Compatibilidad

Se confirmó compatibilidad completa con los servicios previamente implementados:

- RTSP
- RTMP
- HLS
- WebRTC
- MoQ

No se detectaron regresiones durante las pruebas realizadas.

---

## Incidentes

No se registraron incidentes durante la implementación ni durante las pruebas funcionales.

---


- srtReadPassphrase
- srtPublishPassphrase

Durante esta misión dichos mecanismos permanecieron deshabilitados al no formar parte del alcance funcional definido para la plataforma.


## Estado de la misión

**MISSION-013 finalizada satisfactoriamente.**

La plataforma incorpora soporte operativo para Secure Reliable Transport (SRT), completamente validado e integrado dentro de la arquitectura EJTV Broadcast Platform.