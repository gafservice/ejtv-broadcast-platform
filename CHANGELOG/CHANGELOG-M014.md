# MISSION-014 — HTTP Live Streaming (HLS)

**Fecha:** 2026-06-30

## Objetivo

Implementar, validar e integrar el servicio **HTTP Live Streaming (HLS)** dentro de la plataforma **EJTV Broadcast Platform**, utilizando las capacidades nativas de MediaMTX para la distribución de contenido mediante HTTP.

## Implementación

- Se verificó la configuración HLS incluida en MediaMTX v1.19.0.
- Se confirmó la operación del servicio HLS sobre el puerto **8888/TCP**.
- Se habilitó el acceso al servicio mediante UFW.
- Se validó la publicación de un flujo de prueba utilizando FFmpeg mediante RTMP.
- Se comprobó la generación automática del archivo `index.m3u8`.
- Se verificó la creación dinámica de las listas de reproducción utilizadas por el servicio HLS.
- Se confirmó la distribución del flujo mediante HTTP.

## Validación

Se realizaron las siguientes pruebas de funcionamiento:

- Verificación del servicio MediaMTX.
- Verificación del puerto HLS (`8888/TCP`).
- Validación del archivo `index.m3u8`.
- Reproducción satisfactoria mediante VLC.
- Reproducción satisfactoria mediante navegador web.
- Validación del script de mantenimiento `hls-status.sh`.

Todas las pruebas fueron completadas satisfactoriamente.

## Documentación

Se incorporó la documentación técnica del servicio en:

```
docs/services/hls.md
```

La documentación incluye:

- arquitectura del servicio;
- configuración utilizada;
- procedimiento de implementación;
- validación funcional;
- evidencia experimental;
- observaciones técnicas;
- acceptance test;
- revisión técnica final.

## Scripts

Se agregó el script de mantenimiento:

```
scripts/maintenance/hls-status.sh
```

Funciones principales:

- Verificar el estado del servicio MediaMTX.
- Verificar disponibilidad del puerto HLS.
- Validar la respuesta HTTP del servicio.
- Confirmar la existencia de una playlist HLS válida.

## Compatibilidad

La implementación del servicio HLS no requirió modificaciones sobre los servicios previamente validados:

- RTSP
- RTMP
- SRT

La arquitectura existente mantiene plena compatibilidad con el nuevo servicio.

## Estado

**MISSION-014 completada satisfactoriamente.**