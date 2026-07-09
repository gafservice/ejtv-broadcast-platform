# Acceptance Test
# MISSION-015 — WebRTC

**Proyecto:** EJTV Broadcast Platform

**Misión:** MISSION-015

**Servicio:** WebRTC

**Versión MediaMTX:** v1.19.2

**Estado:** APROBADO

---

# Objetivo

Verificar la correcta implementación, configuración y funcionamiento del
servicio WebRTC dentro de la plataforma EJTV Broadcast Platform,
garantizando la distribución de contenido audiovisual hacia navegadores
compatibles mediante MediaMTX.

---

# Alcance

La presente prueba valida:

- Configuración del servicio WebRTC.
- Publicación de un flujo RTSP mediante FFmpeg.
- Conversión automática hacia WebRTC.
- Conversión automática hacia HLS.
- Negociación ICE.
- Establecimiento de Peer Connection.
- Recepción de video.
- Recepción de audio.
- Compatibilidad con la arquitectura existente.

---

# Ambiente de prueba

| Parámetro | Valor |
|-----------|-------|
| Plataforma | EJTV Broadcast Platform |
| Sistema Operativo | Ubuntu Server 24.04.4 LTS |
| MediaMTX | v1.19.2 |
| FFmpeg | 6.1.1 |
| Cliente | Navegador Web |
| Red | LAN Gigabit |

---

# Prerrequisitos

Antes de ejecutar esta prueba deberá verificarse:

- Ubuntu Server operativo.
- MediaMTX v1.19.2 instalado.
- FFmpeg con soporte libx264.
- FFmpeg con soporte libopus.
- Firewall habilitado.
- Puerto TCP 8889 permitido.
- Puerto UDP 8189 permitido.
- Navegador compatible con WebRTC.

---

# Configuración validada

| Parámetro | Estado |
|-----------|:------:|
| WebRTC habilitado | ✅ |
| Listener HTTP 8889 | ✅ |
| Listener ICE UDP 8189 | ✅ |
| Additional Hosts configurado | ✅ |
| Allow Origins habilitado | ✅ |

---

# Procedimiento

---

## Prueba 1 — Verificar versión

Ejecutar:

```bash
/opt/ejtv/mediamtx/bin/mediamtx --version
```

Resultado esperado

```text
v1.19.2
```

Resultado obtenido

✅ Correcto.

---

## Prueba 2 — Verificar servicio

Ejecutar:

```bash
sudo systemctl status mediamtx
```

Resultado esperado

Servicio activo.

Resultado obtenido

✅ Correcto.

---

## Prueba 3 — Verificar configuración

Ejecutar:

```bash
grep -nE "webrtc|8189|8889|webrtcAdditionalHosts" \
/opt/ejtv/mediamtx/config/mediamtx.yml
```

Resultado esperado

Debe observarse:

- WebRTC habilitado.
- Listener HTTP.
- Listener ICE.
- Additional Hosts configurado.

Resultado obtenido

✅ Correcto.

---

## Prueba 4 — Verificar listeners

Ejecutar:

```bash
sudo ss -lntup | grep -E "8889|8189"
```

Resultado esperado

Debe observarse:

TCP 8889

UDP 8189

Resultado obtenido

✅ Correcto.

---

## Prueba 5 — Publicar flujo RTSP

Ejecutar:

```bash
ffmpeg -re \
-f lavfi -i testsrc2=size=640x360:rate=25 \
-f lavfi -i sine=frequency=1000:sample_rate=48000 \
-c:v libx264 \
-profile:v baseline \
-level 3.1 \
-preset ultrafast \
-tune zerolatency \
-pix_fmt yuv420p \
-g 25 \
-keyint_min 25 \
-sc_threshold 0 \
-b:v 800k \
-maxrate 800k \
-bufsize 1600k \
-c:a libopus \
-b:a 96k \
-ar 48000 \
-ac 2 \
-f rtsp \
rtsp://localhost:8554/live/webrtc-test
```

Resultado esperado

MediaMTX publica correctamente el flujo.

Resultado obtenido

✅ Correcto.

---

## Prueba 6 — Verificar HLS

Abrir desde un navegador:

```
http://SERVIDOR:8888/live/webrtc-test/
```

Resultado esperado

El navegador reproduce correctamente el video y el audio mediante HLS.

Resultado obtenido

✅ Correcto.

---

## Prueba 7 — Verificar WebRTC

Abrir desde un navegador:

```
http://SERVIDOR:8889/live/webrtc-test/
```

Resultado esperado

El navegador establece una sesión WebRTC reproduciendo correctamente:

- Video H.264.
- Audio Opus.

Resultado obtenido

✅ Correcto.

---

## Prueba 8 — Verificar registros

Ejecutar:

```bash
sudo journalctl -u mediamtx -n 80 --no-pager
```

Resultado esperado

Debe observarse:

```text
stream is available

peer connection established

is reading from path
```

Resultado obtenido

✅ Correcto.

---

## Prueba 9 — Verificar tráfico ICE

Ejecutar:

```bash
sudo tcpdump -ni any udp port 8189
```

Resultado esperado

Debe observarse intercambio bidireccional de paquetes UDP correspondientes
a la negociación ICE.

Resultado obtenido

✅ Correcto.

---

# Resultados

| Verificación | Estado |
|--------------|:------:|
| MediaMTX iniciado | ✅ |
| Configuración WebRTC | ✅ |
| Listener HTTP | ✅ |
| Listener ICE | ✅ |
| Publicación RTSP | ✅ |
| Conversión HLS | ✅ |
| Conversión WebRTC | ✅ |
| Negociación ICE | ✅ |
| Peer Connection | ✅ |
| Video H264 | ✅ |
| Audio Opus | ✅ |
| Navegador compatible | ✅ |

---

# Incidencias encontradas

Durante las primeras pruebas utilizando MediaMTX v1.19.0 se observó que
las sesiones WebRTC finalizaban con el mensaje:

```
deadline exceeded while waiting connection
```

Después del proceso de diagnóstico se determinó que la implementación
WebRTC incluida en dicha versión presentaba un problema durante la
negociación ICE.

Como acción correctiva se actualizó MediaMTX a la versión v1.19.2.

Posteriormente se verificó el establecimiento exitoso de la Peer
Connection mediante el registro:

```
peer connection established
```

confirmando el correcto funcionamiento del servicio WebRTC.

---

# Evidencias

Durante la ejecución de esta prueba deberán conservarse:

- Estado del servicio MediaMTX.
- Salida de systemctl status.
- Salida de ss.
- Configuración WebRTC.
- Captura reproduciendo HLS.
- Captura reproduciendo WebRTC.
- Salida de journalctl.
- Captura del tráfico ICE mediante tcpdump.
- Versión instalada de MediaMTX.

Las evidencias deberán almacenarse en:

```
docs/evidencias/mission-015/
```

---

# Criterios de aceptación

La misión se considera aprobada únicamente cuando se verifica:

- Servicio WebRTC operativo.
- Configuración correcta.
- Publicación RTSP exitosa.
- Conversión automática RTSP → WebRTC.
- Conversión automática RTSP → HLS.
- Negociación ICE completada.
- Peer Connection establecida.
- Recepción simultánea de video y audio.
- Compatibilidad con la arquitectura EJTV Broadcast Platform.

---

# Resultado final

## MISSION-015

**ACEPTADA**

El servicio WebRTC quedó implementado, validado e integrado oficialmente
a la plataforma EJTV Broadcast Platform.

---

# Checklist final

- [x] Servicio iniciado.
- [x] Configuración validada.
- [x] Publicación RTSP.
- [x] Conversión HLS.
- [x] Conversión WebRTC.
- [x] Negociación ICE.
- [x] Peer Connection establecida.
- [x] Audio recibido.
- [x] Video recibido.
- [x] Evidencias almacenadas.
- [x] Documentación completada.