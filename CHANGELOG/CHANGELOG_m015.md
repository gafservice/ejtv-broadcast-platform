# CHANGELOG-M015

## MISSION-015 — WebRTC

**Fecha:** 30 de junio de 2026

**Estado:** COMPLETADA

---

# Objetivo

Implementar, configurar, validar y documentar completamente el servicio
WebRTC sobre MediaMTX, permitiendo la distribución de contenido
audiovisual de muy baja latencia directamente hacia navegadores
compatibles, integrándolo oficialmente dentro de la infraestructura de la
EJTV Broadcast Platform.

---

# Estado inicial

Al inicio de la misión la plataforma disponía de los siguientes servicios
operativos:

- Ubuntu Server 24.04.4 LTS
- SSH
- Cockpit
- Firewall UFW
- NTP
- MediaMTX v1.19.0
- FFmpeg 6.1.1

Protocolos previamente implementados:

- RTSP
- RTMP
- SRT
- HLS

---

# Implementación

Durante esta misión se habilitó el servicio WebRTC de MediaMTX mediante la
configuración correspondiente del servidor.

Se verificó el funcionamiento del listener HTTP para WebRTC y del listener
ICE sobre UDP, manteniendo compatibilidad con la arquitectura previamente
implementada.

Se validó la publicación de flujos RTSP utilizando FFmpeg como publicador
de referencia y su conversión automática hacia WebRTC.

---

# Diagnóstico técnico

Durante las primeras pruebas utilizando MediaMTX v1.19.0 se observó que
las sesiones WebRTC iniciaban correctamente, pero finalizaban durante la
negociación ICE.

Los registros del servidor mostraban repetidamente el mensaje:

```
closed: deadline exceeded while waiting connection
```

Con el objetivo de identificar el origen del problema se realizaron las
siguientes actividades de diagnóstico:

- Revisión de la configuración WebRTC.
- Validación de codecs.
- Conversión del audio hacia Opus.
- Captura de tráfico ICE mediante tcpdump.
- Verificación de puertos mediante ss.
- Revisión de registros mediante journalctl.
- Validación del firewall UFW.
- Verificación del flujo multimedia utilizando HLS.

Las pruebas permitieron descartar problemas de conectividad,
configuración del servidor o publicación del flujo multimedia.

---

# Actualización de MediaMTX

Como resultado del proceso de diagnóstico se decidió actualizar MediaMTX
desde la versión 1.19.0 hacia la versión 1.19.2.

Previo a la actualización se generaron respaldos completos del binario y
del archivo de configuración, garantizando la posibilidad de reversión en
caso necesario.

La actualización mantuvo íntegramente la configuración previamente
implementada.

---

# Validación

Una vez instalada la versión 1.19.2 se repitieron todas las pruebas de
funcionamiento.

Los registros del servidor confirmaron correctamente:

```
peer connection established
```

seguido por:

```
is reading from path 'live/webrtc-test'

2 tracks (H264, Opus)
```

Con ello quedó validado el establecimiento de la Peer Connection, la
negociación ICE y la transmisión de audio y video hacia el navegador.

---

# Archivos incorporados

Durante la misión se incorporaron los siguientes documentos y recursos.

## Documentación

- docs/services/webrtc.md

## Acceptance Test

- tests/mission-015-webrtc.md

## Scripts

- scripts/maintenance/webrtc-status.sh

---

# Mejoras incorporadas

- Integración oficial del protocolo WebRTC.
- Distribución multimedia con latencia ultrabaja.
- Compatibilidad con navegadores modernos.
- Conversión automática RTSP → WebRTC.
- Validación de video H.264.
- Validación de audio Opus.
- Validación completa de negociación ICE.
- Incorporación de procedimiento de diagnóstico.
- Incorporación de script de mantenimiento para WebRTC.

---

# Compatibilidad

La implementación mantiene compatibilidad completa con:

- RTSP
- RTMP
- SRT
- HLS
- FFmpeg
- MediaMTX
- Arquitectura de red existente
- Firewall UFW
- Procedimientos de operación previamente documentados

No fue necesario modificar configuraciones previamente validadas,
exceptuando la actualización del binario de MediaMTX hacia la versión
1.19.2.

---

# Resultado

La MISSION-015 concluye satisfactoriamente con la incorporación oficial
del servicio WebRTC dentro de la plataforma EJTV Broadcast Platform.

La infraestructura permite ahora distribuir contenido multimedia mediante
los siguientes protocolos:

- RTSP
- RTMP
- SRT
- HLS
- WebRTC

manteniendo la arquitectura modular y la metodología documental
establecida para el proyecto.

---

# Estado final

**MISSION-015 COMPLETADA**

**Servicio WebRTC implementado.**

**Validación técnica superada.**

**Documentación actualizada.**

**Plataforma preparada para la siguiente misión.**