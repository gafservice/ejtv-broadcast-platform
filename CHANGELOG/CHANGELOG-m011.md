# CHANGELOG

Todos los cambios relevantes realizados sobre la plataforma EJTV Broadcast Platform se registran en este documento siguiendo un criterio cronológico.

---

# 2026-06-29 — MISSION-011

## Tipo

Nueva funcionalidad.

---

## Resumen

Se incorporó **FFmpeg** como herramienta oficial para la generación, procesamiento, análisis y validación de flujos multimedia dentro de la plataforma EJTV Broadcast Platform.

La misión concluyó con la integración funcional entre FFmpeg y MediaMTX, estableciendo la base para las pruebas de transmisión de la plataforma.

---

## Diagnóstico

Se verificó el estado del entorno antes de iniciar la instalación.

### Plataforma validada

* Ubuntu Server 24.04.4 LTS.
* Kernel Linux 6.17.0-35-generic.
* Arquitectura x86_64.
* Apple MacPro5,1.
* Intel Xeon W3530.
* Recursos suficientes de memoria y almacenamiento.

### Componentes existentes

Se confirmó el correcto funcionamiento de:

* SSH.
* Cockpit.
* UFW.
* systemd-timesyncd.
* MediaMTX v1.19.0.

También se verificó que FFmpeg, FFprobe y FFplay no se encontraban instalados.

---

## Instalación

Se incorporó FFmpeg utilizando los repositorios oficiales de Ubuntu.

Paquete instalado:

* ffmpeg 6.1.1-3ubuntu5

La instalación incluyó automáticamente:

* ffmpeg
* ffprobe
* ffplay

junto con las bibliotecas principales de la suite FFmpeg.

---

## Verificación

Se verificó correctamente:

* ubicación de los binarios;
* versiones instaladas;
* paquetes registrados mediante APT;
* disponibilidad de FFprobe;
* disponibilidad de FFplay.

---

## Validación técnica

Se confirmó soporte para los protocolos:

* RTMP
* RTMPS
* RTSP
* HTTP
* HTTPS
* TCP
* UDP
* SRT
* SRTP

Se verificó disponibilidad de los códecs:

* H.264
* H.265 / HEVC
* AAC
* Opus

Así como los codificadores:

* libx264
* libx265
* libopus

Y soporte para los formatos:

* FLV
* MPEG-TS
* MP4
* Matroska
* HLS

Adicionalmente se validó:

* primera publicación RTMP;
* primera reproducción RTSP;
* validación mediante FFplay;
* validación mediante FFprobe;
* integración funcional FFmpeg ↔ MediaMTX.

---

## Compatibilidad

Se confirmó que la instalación de FFmpeg es completamente compatible con la infraestructura multimedia previamente implementada mediante MediaMTX.

La plataforma quedó preparada para la implementación de los distintos protocolos de distribución soportados por MediaMTX.

---

## Documentación incorporada

Se incorporó la documentación correspondiente a la misión:

* `docs/services/ffmpeg.md`
* `docs/missions/MISSION-011.md`
* `docs/baseline/BL-006.md`
* `scripts/maintenance/ffmpeg-status.sh`

---

## Incidentes

Durante la instalación volvió a aparecer el incidente conocido asociado al paquete:

```text
broadcom-sta-dkms
```

Este incidente continúa documentado desde la MISSION-004 y no afecta el funcionamiento de FFmpeg.

---

## Estado de la misión

**MISSION-011 finalizada satisfactoriamente.**

FFmpeg quedó completamente integrado dentro de la plataforma EJTV Broadcast Platform y validado para la generación, publicación, reproducción y análisis de flujos multimedia, manteniendo compatibilidad con MediaMTX y sirviendo como base para las siguientes misiones relacionadas con los protocolos de transmisión.