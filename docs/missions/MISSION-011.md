# MISSION-011 — Instalación y Validación de FFmpeg

> Estado: **En progreso**

**Fecha de inicio:** 2026-06-29

---

# Objetivo

Incorporar FFmpeg como herramienta oficial de generación, procesamiento, análisis y validación de flujos multimedia dentro de la plataforma EJTV Broadcast Platform.

La misión comprende el diagnóstico del entorno, la instalación desde los repositorios oficiales de Ubuntu, la verificación de la instalación, la validación de protocolos y códecs disponibles, y la preparación del entorno para las futuras pruebas de integración con MediaMTX.

---

# Antecedentes

Al finalizar la MISSION-010 la plataforma disponía de:

* Ubuntu Server 24.04.4 LTS.
* SSH operativo.
* Cockpit instalado.
* Firewall UFW configurado.
* Sincronización horaria mediante systemd-timesyncd.
* MediaMTX v1.19.0 instalado y ejecutándose como servicio systemd.
* Documentación técnica consolidada.

La siguiente etapa consistía en incorporar una herramienta que permitiera generar flujos multimedia controlados para validar la infraestructura de transmisión.

Después de evaluar las alternativas disponibles se seleccionó FFmpeg debido a su amplia adopción en la industria audiovisual, su compatibilidad con múltiples protocolos y códecs, y su integración con los repositorios oficiales de Ubuntu.

---

# Diagnóstico inicial

Se verificó el estado general del servidor antes de iniciar la instalación.

## Plataforma

* Ubuntu Server 24.04.4 LTS.
* Kernel Linux 6.17.0-35-generic.
* Arquitectura x86_64.
* Hardware Apple MacPro5,1.
* CPU Intel Xeon W3530.
* Recursos suficientes de memoria y almacenamiento.

## Verificación de FFmpeg

Se comprobó la ausencia de los componentes principales.

```bash
which ffmpeg
which ffprobe
which ffplay
```

Resultado:

* FFmpeg no instalado.
* FFprobe no instalado.
* FFplay no instalado.

## Repositorios

Se verificó la disponibilidad del paquete oficial.

```bash
apt-cache policy ffmpeg
```

Versión candidata:

```
7:6.1.1-3ubuntu5
```

## Estado de MediaMTX

Se confirmó que MediaMTX permanecía operativo antes de iniciar la instalación.

```bash
systemctl status mediamtx
```

El servicio se encontraba activo y escuchando en los puertos configurados.

---

# Decisión técnica

Se decidió instalar FFmpeg utilizando exclusivamente los repositorios oficiales de Ubuntu.

Esta decisión se fundamentó en los siguientes criterios:

* estabilidad;
* mantenimiento simplificado;
* integración con APT;
* actualizaciones automáticas mediante el sistema operativo;
* soporte oficial de Ubuntu;
* reducción del esfuerzo de mantenimiento.

La compilación manual queda reservada para futuras necesidades específicas que requieran funcionalidades no incluidas en la versión distribuida por Ubuntu.

---

# Implementación

## Actualización del índice de paquetes

```bash
sudo apt update
```

## Instalación

```bash
sudo apt install -y ffmpeg
```

Durante la instalación se presentó nuevamente el incidente previamente documentado relacionado con el paquete:

```
broadcom-sta-dkms
```

Este incidente ya había sido identificado durante la MISSION-004 y no afecta el funcionamiento de FFmpeg.

---

# Verificación de la instalación

## Binarios instalados

```bash
which ffmpeg
which ffprobe
which ffplay
```

Resultado:

```
/usr/bin/ffmpeg
/usr/bin/ffprobe
/usr/bin/ffplay
```

## Verificación de versiones

```bash
ffmpeg -version
ffprobe -version
ffplay -version
```

Resultado:

* FFmpeg 6.1.1
* FFprobe 6.1.1
* FFplay 6.1.1

Todos los componentes quedaron correctamente instalados.

---

# Validación técnica

Se verificó la disponibilidad de los principales protocolos utilizados por la plataforma.

## Protocolos

```bash
ffmpeg -protocols
```

Se confirmó soporte para:

* RTMP
* RTMPS
* RTSP
* HTTP
* HTTPS
* TCP
* UDP
* SRT
* SRTP

## Códecs

```bash
ffmpeg -codecs
```

Se verificó disponibilidad de:

* H.264
* H.265 / HEVC
* AAC
* Opus

## Encoders

```bash
ffmpeg -encoders
```

Se confirmó la presencia de:

* libx264
* libx265
* AAC
* libopus

## Formatos

```bash
ffmpeg -formats
```

Se verificó compatibilidad con:

* FLV
* MPEG-TS
* MP4
* Matroska
* HLS
* RTSP

La instalación satisface completamente los requerimientos definidos para las siguientes fases del proyecto.

---

# Incidentes observados

Durante la instalación apareció nuevamente el error asociado al paquete:

```
broadcom-sta-dkms
```

El incidente no impidió la instalación de FFmpeg y continúa documentado como un problema independiente originado durante la actualización del sistema.

No se detectaron problemas asociados directamente a FFmpeg.

---

# Estado alcanzado

Al finalizar esta etapa la plataforma dispone de:

* FFmpeg instalado.
* FFprobe instalado.
* FFplay instalado.
* Protocolos multimedia validados.
* Códecs principales disponibles.
* Integración preparada para MediaMTX.

---

# Evidencias generadas

Las verificaciones realizadas incluyeron:

* diagnóstico del entorno;
* instalación mediante APT;
* verificación de binarios;
* comprobación de versiones;
* validación de protocolos;
* validación de códecs;
* validación de formatos;
* comprobación de dependencias instaladas.

---

# Lecciones aprendidas

La versión oficial distribuida por Ubuntu proporciona todas las capacidades necesarias para las etapas actuales del proyecto, eliminando la necesidad de compilar FFmpeg manualmente.

Asimismo, quedó confirmado que el incidente relacionado con Broadcom corresponde a un problema independiente que no compromete la operación de FFmpeg.

---

# Pendientes

Los siguientes trabajos forman parte de la continuación de la misión:

* integración funcional con MediaMTX;
* primera transmisión RTMP de prueba;
* primera recepción mediante FFplay;
* creación de TEST-007;
* elaboración del script `ffmpeg-status.sh`;
* actualización de la línea base correspondiente;
* actualización del CHANGELOG;
* cierre formal de la misión.

---

# Estado de la misión

**Estado actual:** En progreso.

La instalación y validación de FFmpeg fueron completadas satisfactoriamente.

La misión permanecerá abierta hasta finalizar las pruebas funcionales de integración con MediaMTX y completar toda la documentación asociada.


## Validación funcional

Se realizó una prueba extremo a extremo utilizando:

FFmpeg
↓ RTMP
MediaMTX
↓ RTSP
FFplay
↓
FFprobe

Resultados

✓ Publicación RTMP
✓ Conversión automática RTMP→RTSP
✓ Decodificación H264
✓ Decodificación AAC
✓ Reproducción continua
✓ Inspección mediante FFprobe