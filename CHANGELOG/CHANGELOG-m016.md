# CHANGELOG-M016

## MISSION-016 — End-to-End Validation

**Fecha:** 2026-07-01

**Estado:** Finalizada

---

# Objetivo

Realizar la validación integral de la plataforma multimedia EJTV Broadcast Platform verificando el funcionamiento conjunto de todos los protocolos implementados sobre MediaMTX.

---

# Validaciones realizadas

## Infraestructura

- Validación de Ubuntu Server 24.04.4 LTS.
- Verificación de sincronización mediante systemd-timesyncd.
- Confirmación del funcionamiento de MediaMTX v1.19.2.
- Confirmación de FFmpeg 6.1.1.
- Verificación de puertos de servicio.

---

## Protocolos

Se validó correctamente la operación de:

- RTSP
- RTMP
- SRT
- HLS
- WebRTC

---

## Interoperabilidad

Se comprobó que un único flujo multimedia publicado mediante RTSP es redistribuido correctamente por MediaMTX hacia todos los protocolos soportados.

---

## Validación simultánea

Se verificó la operación concurrente de:

- RTSP
- RTMP
- SRT
- HLS
- WebRTC

sin afectar la estabilidad de la plataforma.

---

## Rendimiento

Durante la prueba se verificó:

- consumo de CPU;
- consumo de memoria;
- estabilidad de MediaMTX;
- estabilidad de FFmpeg;
- ausencia de reinicios inesperados.

---

## Hallazgos

### RTMP

RTMP omite la pista Opus debido a limitaciones propias del protocolo.

Se recomienda AAC para despliegues RTMP de producción.

---

### HLS

La validación funcional se realizó mediante ffprobe.

Las solicitudes HTTP HEAD utilizando curl pueden devolver 404 en modo Low-Latency HLS y no constituyen un fallo del servicio.

---

### WebRTC

Los eventos:

```
deadline exceeded while waiting connection
```

correspondieron a intentos de negociación ICE no completados durante pruebas iniciales.

Una vez establecida la conexión WebRTC, no volvieron a registrarse dichos eventos.

---

### HEVC

Se realizó una validación complementaria utilizando:

- HEVC
- 1920×1080
- AAC

La prueba confirmó el transporte correcto mediante RTSP y SRT.

La validación definitiva de señales broadcast 1080i59.94 provenientes de equipamiento profesional queda propuesta para futuras misiones.

---

# Resultado

MISSION-016 concluye con la validación integral de la plataforma multimedia EJTV Broadcast Platform demostrando la correcta operación conjunta de RTSP, RTMP, SRT, HLS y WebRTC sobre una arquitectura unificada basada en MediaMTX y FFmpeg.
