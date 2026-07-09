# TEST-007 — Verificación de instalación y capacidades de FFmpeg

> **Estado:** Pendiente de ejecución

> **Misión asociada:** MISSION-011

> **Fecha:** 2026-06-29

---

# Objetivo

Verificar que FFmpeg fue instalado correctamente en la plataforma EJTV Broadcast Platform y que dispone de los protocolos, códecs, formatos y herramientas necesarias para soportar las siguientes etapas del proyecto.

Este procedimiento constituye la prueba oficial de aceptación de la instalación de FFmpeg.

---

# Alcance

Este test valida:

* instalación del paquete;
* disponibilidad de los binarios;
* versión instalada;
* protocolos soportados;
* códecs disponibles;
* formatos multimedia;
* integración con el sistema operativo.

No incluye aún pruebas de transmisión con MediaMTX, las cuales serán documentadas en pruebas posteriores.

---

# Requisitos

Antes de iniciar esta prueba deben cumplirse las siguientes condiciones.

* Ubuntu Server operativo.
* Acceso administrativo.
* Repositorios oficiales configurados.
* MISSION-011 ejecutada hasta la fase de instalación.

---

# Procedimiento

## Prueba 1 — Verificación de binarios

Ejecutar:

```bash
which ffmpeg
which ffprobe
which ffplay
```

Resultado esperado:

```text
/usr/bin/ffmpeg
/usr/bin/ffprobe
/usr/bin/ffplay
```

Resultado:

□ Aprobado

□ Rechazado

---

## Prueba 2 — Verificación de versión

Ejecutar:

```bash
ffmpeg -version
```

Resultado esperado:

* versión 6.1.1 (o superior aprobada por el proyecto);
* compilación oficial de Ubuntu;
* ejecución sin errores.

Resultado:

□ Aprobado

□ Rechazado

---

## Prueba 3 — FFprobe

Ejecutar:

```bash
ffprobe -version
```

Resultado esperado:

La utilidad responde correctamente mostrando su versión.

Resultado:

□ Aprobado

□ Rechazado

---

## Prueba 4 — FFplay

Ejecutar:

```bash
ffplay -version
```

Resultado esperado:

La utilidad responde correctamente mostrando su versión.

Resultado:

□ Aprobado

□ Rechazado

---

## Prueba 5 — Protocolos

Ejecutar:

```bash
ffmpeg -protocols
```

Verificar disponibilidad de:

* RTMP
* RTMPS
* RTSP
* HTTP
* HTTPS
* TCP
* UDP
* SRT
* SRTP

Resultado:

□ Aprobado

□ Rechazado

---

## Prueba 6 — Códecs

Ejecutar:

```bash
ffmpeg -codecs
```

Verificar:

Video

* H.264
* H.265

Audio

* AAC
* Opus

Resultado:

□ Aprobado

□ Rechazado

---

## Prueba 7 — Encoders

Ejecutar:

```bash
ffmpeg -encoders
```

Verificar:

* libx264
* libx265
* AAC
* libopus

Resultado:

□ Aprobado

□ Rechazado

---

## Prueba 8 — Formatos

Ejecutar:

```bash
ffmpeg -formats
```

Verificar soporte para:

* FLV
* MPEG-TS
* MP4
* Matroska
* HLS

Resultado:

□ Aprobado

□ Rechazado

---

## Prueba 9 — Estado del paquete

Ejecutar:

```bash
dpkg -l | grep ffmpeg
```

Resultado esperado:

El paquete aparece instalado correctamente.

Resultado:

□ Aprobado

□ Rechazado

---

## Prueba 10 — Auditoría del sistema

Ejecutar:

```bash
sudo dpkg --audit
```

Resultado esperado:

No deben aparecer errores relacionados con FFmpeg.

Puede aparecer el incidente conocido correspondiente a:

```text
broadcom-sta-dkms
```

Este incidente no invalida la prueba.

Resultado:

□ Aprobado

□ Rechazado

---

# Resultado global

| Prueba     | Estado |
| ---------- | :----: |
| Binarios   |    □   |
| Versiones  |    □   |
| FFprobe    |    □   |
| FFplay     |    □   |
| Protocolos |    □   |
| Códecs     |    □   |
| Encoders   |    □   |
| Formatos   |    □   |
| Paquete    |    □   |
| Auditoría  |    □   |

---

# Criterio de aceptación

La prueba se considera satisfactoria cuando:

* todas las verificaciones relacionadas con FFmpeg son aprobadas;
* los binarios funcionan correctamente;
* los protocolos requeridos están disponibles;
* los códecs definidos por el proyecto están presentes;
* no existen errores asociados a FFmpeg.

El incidente previamente documentado relacionado con **broadcom-sta-dkms** no constituye un criterio de rechazo para esta prueba.

---

# Evidencias

Registrar:

* salida de `ffmpeg -version`;
* salida de `ffprobe -version`;
* salida de `ffplay -version`;
* protocolos detectados;
* códecs detectados;
* resultado de `dpkg -l`;
* resultado de `sudo dpkg --audit`.

---

# Observaciones

Esta prueba valida exclusivamente la instalación y las capacidades de FFmpeg.

Las pruebas de transmisión mediante RTMP, RTSP, SRT, HLS y WebRTC se documentarán en los procedimientos de prueba correspondientes de la fase multimedia.

---

# Aprobación

| Elemento                | Estado |
| ----------------------- | :----: |
| Procedimiento ejecutado |    □   |
| Resultados registrados  |    □   |
| Evidencias archivadas   |    □   |
| Ingeniería aprobada     |    □   |
| Test aprobado           |    □   |

# Prueba 007.2
## Integración FFmpeg + MediaMTX

Objetivo

Validar la publicación RTMP hacia MediaMTX y la reproducción mediante RTSP.

Resultado esperado

- publicación RTMP exitosa;
- MediaMTX acepta el flujo;
- FFplay reproduce el contenido;
- FFprobe identifica correctamente los códecs.

Resultado obtenido

Prueba satisfactoria.

Video:
- H.264 High Profile
- 1280×720
- 30 fps

Audio:
- AAC LC
- 48 kHz
- Mono

Estado

APROBADA


