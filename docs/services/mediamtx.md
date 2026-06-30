# MediaMTX
## Servicio de Streaming de la Plataforma EJTV

**Documento:** docs/services/mediamtx.md

**Versión del documento:** 1.0

**Última actualización:** 2026-06-29

**Componente:** MediaMTX

**Versión instalada:** v1.19.0

**Sistema operativo:** Ubuntu Server 24.04.4 LTS

**Arquitectura:** x86_64

**Estado:** Producción (Laboratorio)

---

# 1. Introducción

## 1.1 Descripción

MediaMTX es el servidor multimedia seleccionado para la plataforma EJTV Broadcast Platform.

Su función consiste en recibir, distribuir, convertir y publicar flujos multimedia utilizando múltiples protocolos de transmisión en tiempo real.

Durante la fase inicial del proyecto se utilizará como servidor central de distribución para pruebas de laboratorio y validación de la arquitectura de transmisión.

La instalación se realizó utilizando el binario oficial distribuido por el proyecto MediaMTX, evitando el uso de contenedores Docker con el fin de simplificar el mantenimiento, reducir dependencias y facilitar el diagnóstico del sistema operativo.

---

# 2. Objetivo del servicio

- Centralizar los flujos multimedia de la plataforma.
- Proporcionar una arquitectura escalable.
- Soportar múltiples protocolos de streaming.
- Facilitar futuras integraciones con OBS Studio.
- Facilitar futuras integraciones con cámaras IP.
- Facilitar futuras integraciones con FFmpeg.
- Proveer una base para distribución WebRTC.
- Servir como núcleo multimedia del sistema EJTV.

---

# 3. Arquitectura dentro de EJTV

(describir completamente la arquitectura)

Servidor Ubuntu

↓

MediaMTX

↓

RTSP
RTMP
HLS
WebRTC
SRT
MoQ

↓

Clientes

OBS
VLC
Navegadores
Aplicaciones móviles
Codificadores

---

# 4. Protocolos soportados

## RTSP

Descripción.

Puerto.

Aplicaciones.

Ventajas.

Desventajas.

---

## RTMP

...

---

## HLS

...

---

## WebRTC

...

---

## SRT

...

---

## MoQ

...

---

# 5. Requisitos

## Hardware

CPU

RAM

Espacio en disco

Arquitectura

---

## Software

Ubuntu

systemd

OpenSSL

wget

tar

sha256sum

tree

journalctl

---

# 6. Descarga oficial

Repositorio oficial

Versión instalada

Comandos ejecutados

```bash
cd /opt/ejtv/mediamtx/releases

MEDIAMTX_VERSION="v1.19.0"

MEDIAMTX_FILE="mediamtx_${MEDIAMTX_VERSION}_linux_amd64.tar.gz"

wget ...

wget ...
```

---

# 7. Verificación SHA256

Explicación

Comandos

```bash
grep ...

sha256sum -c -

sha256sum archivo
```

Resultado esperado

Resultado obtenido

Checksum

---

# 8. Instalación

Crear estructura

```bash
mkdir ...

mkdir ...

mkdir ...
```

Extracción

```bash
tar ...

```

Instalación

```bash
cp ...

chmod ...

tree ...

```

---

# 9. Estructura de directorios

```
/opt/ejtv/mediamtx

├── backup
├── bin
├── config
├── logs
├── recordings
├── releases
├── scripts
└── tests
```

Descripción detallada de cada directorio.

---

# 10. Configuración inicial

Archivo

```
config/mediamtx.yml
```

Ubicación

Parámetros principales

Buenas prácticas

---

# 11. Servicio systemd

Archivo

```
/etc/systemd/system/mediamtx.service
```

Contenido completo del archivo

Explicación línea por línea.

---

# 12. Validación

Todos los comandos utilizados

```bash
systemctl status mediamtx

systemctl is-enabled mediamtx

ps -ef

ss -tuln

journalctl

tree

cat installed_versions.log
```

Resultados esperados

Resultados obtenidos

---

# 13. Pruebas funcionales

Prueba manual

Inicio

Detención

Reinicio

Persistencia

Verificación de puertos

---

# 14. Operación diaria

Iniciar

Detener

Reiniciar

Recargar

Consultar estado

Consultar logs

---

# 15. Diagnóstico

Servicio

Procesos

Puertos

Configuración

Versión

Rutas

---

# 16. Actualización

Procedimiento completo

Descarga

SHA256

Instalación

Prueba

Rollback

---

# 17. Rollback

Cómo regresar a una versión anterior.

---

# 18. Backup

Archivos críticos

Configuraciones

Versiones

Servicio

---

# 19. Troubleshooting

Error

Causa

Diagnóstico

Solución

Agregar todos los problemas encontrados durante la instalación.

---

# 20. Engineering Notes

¿Por qué MediaMTX?

¿Por qué no Docker?

¿Por qué /opt?

¿Por qué systemd?

¿Por qué releases?

¿Por qué mantener versiones?

Riesgos conocidos.

Buenas prácticas.

---

# 21. Checklist final

□ Descarga verificada

□ SHA256 correcto

□ Instalación realizada

□ Configuración instalada

□ Servicio creado

□ Servicio habilitado

□ Servicio iniciado

□ Validación completada

□ Documentación actualizada

□ Baseline actualizada

□ CHANGELOG actualizado

---

# 22. Referencias

Repositorio oficial

https://github.com/bluenviron/mediamtx

Documentación oficial

https://mediamtx.org/

Licencia

Versión

Release utilizada

SHA256

## Ejemplo de publicación

ffmpeg ...

## Ejemplo de reproducción

ffplay rtsp://localhost:8554/live/test

## Ejemplo de inspección

ffprobe rtsp://localhost:8554/live/test

## Validación realizada durante la MISSION-011

Durante la MISSION-011 se realizó la validación funcional de la integración entre
FFmpeg y MediaMTX utilizando una fuente de video sintética generada mediante el
filtro `testsrc` y una señal de audio generada mediante el filtro `sine`.

La transmisión se publicó utilizando el protocolo RTMP y posteriormente fue
recibida mediante RTSP desde el propio servidor MediaMTX.

La prueba permitió verificar el funcionamiento conjunto de ambos componentes y
confirmar la correcta conversión entre protocolos realizada por MediaMTX.

El flujo publicado utilizó las siguientes características:

- Resolución: 1280 × 720
- Frecuencia: 30 fps
- Video: H.264 (libx264)
- Audio: AAC LC
- Muestreo de audio: 48 kHz
- Bitrate de video configurado: 2500 kb/s


## Publicación RTMP

El siguiente comando fue utilizado para publicar un flujo sintético hacia
MediaMTX.

```bash
ffmpeg \
-re \
-f lavfi -i testsrc=size=1280x720:rate=30 \
-f lavfi -i sine=frequency=1000:sample_rate=48000 \
-c:v libx264 \
-preset veryfast \
-tune zerolatency \
-pix_fmt yuv420p \
-g 60 \
-b:v 2500k \
-c:a aac \
-b:a 128k \
-ar 48000 \
-f flv \
rtmp://localhost:1935/live/test
```


## Recepción RTSP

Una vez publicado el flujo, MediaMTX permitió acceder al mismo mediante RTSP.

```bash
ffplay rtsp://localhost:8554/live/test
```

La reproducción fue satisfactoria.



## Inspección del flujo

La verificación de los códecs y parámetros del flujo se realizó mediante FFprobe.

```bash
ffprobe rtsp://localhost:8554/live/test
```

FFprobe detectó correctamente:

- Video H.264 High Profile
- Resolución 1280×720
- 30 fps
- Audio AAC LC
- 48 kHz


## Resultado de la validación

La integración entre FFmpeg y MediaMTX fue validada satisfactoriamente.

Se comprobó:

- publicación RTMP;
- conversión automática RTMP → RTSP;
- reproducción mediante FFplay;
- inspección mediante FFprobe;
- compatibilidad completa entre ambos componentes.

Esta validación constituye la primera prueba multimedia extremo a extremo de la
plataforma EJTV Broadcast Platform.