# FFmpeg

> *"FFmpeg constituye la herramienta principal para la generación, procesamiento,
análisis y transporte de flujos multimedia dentro de la plataforma EJTV Broadcast
Platform."*

---

# Introducción

FFmpeg es un conjunto de herramientas de código abierto ampliamente utilizado
en la industria audiovisual para la captura, procesamiento, codificación,
transcodificación, análisis y transmisión de contenido multimedia.

Dentro de la plataforma EJTV Broadcast Platform, FFmpeg constituye la principal
herramienta de generación y validación de flujos audiovisuales, permitiendo
realizar pruebas controladas antes de incorporar fuentes de video reales.

Su utilización facilita la verificación del correcto funcionamiento del servidor
MediaMTX, así como la evaluación de diferentes protocolos de transporte y
formatos multimedia.

---

# Objetivo

El objetivo de este documento es describir el procedimiento oficial para la
instalación, validación, operación y mantenimiento de FFmpeg dentro de la
plataforma EJTV Broadcast Platform.

Este documento también establece los criterios técnicos utilizados para su
selección y los procedimientos necesarios para futuras actualizaciones.

---

# Función dentro de la plataforma

Dentro de EJTV Broadcast Platform, FFmpeg desempeña múltiples funciones.

Entre ellas:

- generación de señales de prueba;
- publicación de flujos multimedia;
- recepción de transmisiones;
- análisis de medios;
- diagnóstico de protocolos;
- validación de MediaMTX;
- captura de dispositivos;
- transcodificación cuando sea requerida.

Durante las primeras etapas del proyecto FFmpeg será utilizado principalmente
como generador de contenido para validar la infraestructura multimedia.

---

# Arquitectura

La interacción de FFmpeg con el resto de la plataforma puede resumirse mediante
el siguiente esquema.

```
          Cámara
             │
             ▼
         FFmpeg
             │
             ▼
        MediaMTX
             │
 ┌───────────┼─────────────┐
 ▼           ▼             ▼
RTMP       SRT          WebRTC
 ▼           ▼             ▼
Clientes  Operadores   Navegadores
```

---

# Requisitos

Para la instalación oficial se requiere:

- Ubuntu Server 24.04 LTS;
- arquitectura x86_64;
- acceso administrativo;
- conexión a Internet;
- repositorios oficiales habilitados.

---

# Diagnóstico previo

Antes de instalar FFmpeg se recomienda verificar el estado del sistema.

## Sistema operativo

```bash
lsb_release -ds
```

## Kernel

```bash
uname -r
```

## Arquitectura

```bash
uname -m
```

## CPU

```bash
lscpu
```

## Memoria

```bash
free -h
```

## Disco

```bash
df -h /
```

## Verificar instalación previa

```bash
which ffmpeg
which ffplay
which ffprobe
```

## Verificar paquetes

```bash
dpkg -l | grep ffmpeg
```

## Consultar versión disponible

```bash
apt-cache policy ffmpeg
```

---

# Decisión técnica

Para este proyecto se decidió utilizar la versión distribuida por los
repositorios oficiales de Ubuntu.

Las principales razones fueron:

- estabilidad;
- integración con el sistema operativo;
- mantenimiento simplificado;
- actualizaciones mediante APT;
- soporte de seguridad.

La compilación manual queda reservada únicamente para escenarios donde sea
necesario incorporar códecs o funcionalidades no incluidas en la versión oficial.

---

# Instalación

Actualizar el índice de paquetes.

```bash
sudo apt update
```

Instalar FFmpeg.

```bash
sudo apt install -y ffmpeg
```

Durante la instalación puede aparecer un mensaje relacionado con el paquete
**broadcom-sta-dkms**.

Este incidente corresponde a un problema previamente documentado durante la
MISSION-004 y no afecta el funcionamiento de FFmpeg.

---

# Verificación de la instalación

## Localización de los binarios

```bash
which ffmpeg
which ffprobe
which ffplay
```

---

## Versión

```bash
ffmpeg -version
```

---

## FFprobe

```bash
ffprobe -version
```

---

## FFplay

```bash
ffplay -version
```

---

## Paquetes instalados

```bash
dpkg -l | grep ffmpeg
```

---

# Validación técnica

## Protocolos

```bash
ffmpeg -protocols
```

Verificar especialmente:

- RTMP
- RTSP
- HTTP
- HTTPS
- TCP
- UDP
- SRT
- SRTP

---

## Códecs

```bash
ffmpeg -codecs
```

Verificar:

- H264
- HEVC
- AAC
- OPUS

---

## Encoders

```bash
ffmpeg -encoders
```

Verificar:

- libx264
- libx265
- aac
- libopus

---

## Decoders

```bash
ffmpeg -decoders
```

---

## Formatos

```bash
ffmpeg -formats
```

Verificar:

- FLV
- MPEGTS
- MP4
- MATROSKA
- HLS
- RTSP

---

# Integración con MediaMTX

Una vez instalado FFmpeg debe verificarse la integración con MediaMTX.

Se recomienda confirmar previamente que MediaMTX se encuentra operativo.

```bash
systemctl status mediamtx
```

Las pruebas funcionales de transmisión se documentan en:

```
tests/TEST-007-FFmpeg.md
```

---

# Operación diaria

Consultar versión.

```bash
ffmpeg -version
```

Consultar protocolos.

```bash
ffmpeg -protocols
```

Consultar filtros.

```bash
ffmpeg -filters
```

Consultar dispositivos.

```bash
ffmpeg -devices
```

Consultar formatos.

```bash
ffmpeg -formats
```

---

# Diagnóstico

Verificar instalación.

```bash
which ffmpeg
```

Verificar librerías.

```bash
ldd $(which ffmpeg)
```

Verificar paquetes.

```bash
dpkg -l | grep ffmpeg
```

Verificar auditoría del sistema.

```bash
sudo dpkg --audit
```

---

# Actualización

Actualizar índices.

```bash
sudo apt update
```

Actualizar FFmpeg.

```bash
sudo apt upgrade ffmpeg
```

---

# Desinstalación

Eliminar FFmpeg.

```bash
sudo apt remove ffmpeg
```

Eliminar dependencias no utilizadas.

```bash
sudo apt autoremove
```

---

# Troubleshooting

## FFmpeg no inicia

Verificar:

```bash
which ffmpeg
```

---

## Error de librerías

```bash
ldd $(which ffmpeg)
```

---

## Error de paquetes

```bash
sudo dpkg --audit
```

---

## Error durante APT

Si aparece un error asociado a **broadcom-sta-dkms**, consultar la
documentación de la **MISSION-004**.

---

# Engineering Notes

Durante la MISSION-011 se decidió utilizar la versión oficial de Ubuntu por
considerarse suficientemente estable para las necesidades actuales de la
plataforma.

La versión instalada incorpora soporte para los protocolos multimedia utilizados
en el proyecto, incluyendo RTMP, RTSP, SRT, HLS, HTTP y HTTPS, además de los
códecs H.264, H.265, AAC y Opus.

La compilación manual únicamente será considerada cuando futuras necesidades de
la plataforma requieran funcionalidades no disponibles en los repositorios
oficiales.

---

# Checklist

- [ ] Diagnóstico realizado.
- [ ] Instalación completada.
- [ ] FFmpeg verificado.
- [ ] FFprobe verificado.
- [ ] FFplay verificado.
- [ ] Protocolos validados.
- [ ] Códecs validados.
- [ ] Integración con MediaMTX validada.
- [ ] TEST-007 aprobado.
- [ ] Línea base actualizada.
- [ ] CHANGELOG actualizado.